#  Copyright (c) 2022.  NetFoundry, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import ctypes
import os
import platform
from typing import Tuple

_mod_path = os.path.dirname(__file__)
osname = platform.system().lower()

if osname == 'linux':
    LIBNAME = 'libziti.so'
elif osname == 'darwin':
    LIBNAME = 'libziti.dylib'
elif osname == 'windows':
    LIBNAME = 'ziti.dll'
else:
    raise ImportError("could not load ziti shared library")

ziti = ctypes.CDLL(_mod_path + f'/lib/{LIBNAME}')


class _Ver(ctypes.Structure):
    _fields_ = [('version', ctypes.c_char_p), ('revision', ctypes.c_char_p)]

    def __repr__(self):
        return f'({self.version}, {self.revision})'


_ziti_version = ziti.ziti_get_version
_ziti_version.restype = ctypes.POINTER(_Ver)

_ziti_lasterr = ziti.Ziti_last_error

_ziti_errorstr = ziti.ziti_errorstr
_ziti_errorstr.argtypes = [ctypes.c_int]
_ziti_errorstr.restype = ctypes.c_char_p

_load_ctx = ziti.Ziti_load_context
_load_ctx.argtypes = [ctypes.POINTER(ctypes.c_char), ]
_load_ctx.restype = ctypes.c_void_p

ziti_socket = ziti.Ziti_socket
ziti_socket.argtypes = [ctypes.c_int]
ziti_socket.restype = ctypes.c_int

_ziti_connect = ziti.Ziti_connect
_ziti_connect.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p]

_ziti_connect_addr = ziti.Ziti_connect_addr
_ziti_connect_addr.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
_ziti_connect_addr.restype = ctypes.c_int

_ziti_bind = ziti.Ziti_bind
_ziti_bind.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p]

_ziti_listen = ziti.Ziti_listen
_ziti_listen.argtypes = [ctypes.c_int, ctypes.c_int]

_ziti_accept = ziti.Ziti_accept
_ziti_accept.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]

_ziti_enroll = ziti.Ziti_enroll_identity
_ziti_enroll.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.POINTER(ctypes.c_size_t)
]
_ziti_enroll.restype = ctypes.c_int

def free_win32(arg):
    pass

if osname != 'windows':
    _free = ziti.free
    _free.argtypes = [ctypes.c_void_p]
else:
    _free = free_win32

def version():
    ver = _ziti_version().contents
    return ver


def errorstr(code):
    msg = _ziti_errorstr(code)
    return msg.decode()


def check_error(code):
    if code != 0:
        err = _ziti_lasterr()
        if err < 0:
            msg = _ziti_errorstr(err).decode(encoding='utf-8')
        else:
            msg = errorstr(err)
        raise Exception(err, msg)


def init():
    ziti.Ziti_lib_init()


def shutdown():
    ziti.Ziti_lib_shutdown()


def load(path):
    init()
    b_obj = bytes(path, encoding="utf-8")
    return _load_ctx(b_obj)


def connect(fd, ztx, service: str):
    srv = bytes(service, encoding='utf-8')
    check_error(_ziti_connect(fd, ztx, srv))


def connect_addr(fd, addr: Tuple[str, int]):
    host = bytes(addr[0], encoding='utf-8')
    port = addr[1]
    check_error(_ziti_connect_addr(fd, host, port))


def bind(fd, ztx, service):
    srv = bytes(service, encoding='utf-8')
    check_error(_ziti_bind(fd, ztx, srv))


def listen(fd, backlog):
    check_error(_ziti_listen(fd, backlog))


def accept(fd):
    b = ctypes.create_string_buffer(128)
    clt = _ziti_accept(fd, b, 128)
    if clt < 0:
        check_error(clt)
    return clt, (bytes(b.value).decode('utf-8'), 0)


def enroll(jwt, key=None, cert=None):
    init()
    try:
        with open(jwt, 'rb') as jwt_f:
            jwtc = bytes(jwt_f.read())
    except:
        jwtc = bytes(jwt, 'utf-8')

    id_json = ctypes.c_char_p()
    id_json_len = ctypes.c_size_t()
    retcode = _ziti_enroll(jwtc, key, cert,
                           ctypes.byref(id_json),
                           ctypes.byref(id_json_len))
    if retcode != 0:
        raise RuntimeError(errorstr(retcode))
    try:
        return id_json.value.decode()
    finally:
        _free(id_json)
