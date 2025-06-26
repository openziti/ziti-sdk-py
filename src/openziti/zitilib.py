#  Copyright (c) 2022.  NetFoundry Inc.
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

# pylint: disable=no-member

import ctypes
import os
import platform
import socket
from typing import Optional, Tuple

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

zitilib_path = _mod_path + f'/lib/{LIBNAME}'
ziti = ctypes.CDLL(zitilib_path)


class _Ver(ctypes.Structure):
    _fields_ = [('version', ctypes.c_char_p), ('revision', ctypes.c_char_p)]

    def __repr__(self):
        return f'({self.version}, {self.revision})'


class SockAddrIn(ctypes.Structure):
    """
    maps struct sockaddr_in

    NOTE:
    -----
    On Linux/Win32 the first two bytes are address family as short,
    on Darwin the first two bytes.
    """
    _fields_ = [
        ('_family', ctypes.c_uint8 * 2),
        ('_port', ctypes.c_uint16),
        ('_addr', ctypes.c_uint8 * 4)
    ]

    def ip(self):
        return '.'.join(str(o) for o in self._addr)

    def af(self):
        fam = self._family[0]
        if osname == 'darwin':
            fam = self._family[1]
        return socket.AddressFamily(fam)

    @property
    def port(self):
        return socket.ntohs(self._port)
    def __repr__(self):
        return f'{self.af().name}:{self.ip()}:{self.port}'


class _AddrInfo(ctypes.Structure):
    """
    int ai_flags;              /* Input flags. */
    int ai_family;             /* Protocol family for socket. */
    int ai_socktype;           /* Socket type. */
    int ai_protocol;           /* Protocol for socket. */
    socklen_t ai_addrlen;      /* Length of socket address. */
    struct sockaddr *ai_addr;  /* Socket address for socket. */
    char *ai_canonname;        /* Canonical name for service location. */
    struct addrinfo *ai_next;  /* Pointer to next in list. */

    NOTE:
    -----
    The order of ai_addr and ai_canonname is switched on
    Darwin and Windows compared to Linux.
    """
    _fields_ = [
        ('ai_flags', ctypes.c_int),
        ('ai_family', ctypes.c_int),
        ('ai_socktype', ctypes.c_int),
        ('ai_protocol', ctypes.c_int),
        ('ai_addrlen', ctypes.c_int32),
        ('ai_p1', ctypes.c_void_p),
        ('ai_p2', ctypes.c_void_p),
        ('ai_next', ctypes.c_void_p)
    ]

    def get_addr(self):
        addr_p = self.ai_p2
        if osname == 'linux':
            addr_p = self.ai_p1
        if addr_p is None:
            return None
        return SockAddrIn.from_address(addr_p)

    def get_canonname(self):
        p = self.ai_p1
        if osname == 'linux':
            p = self.ai_p2
        if p is None:
            return None
        return str(ctypes.cast(p, ctypes.c_char_p))

    def __repr__(self):
        return '|'.join((x[0] + '=' + str(getattr(self, x[0])))
                        for x in _AddrInfo._fields_)


_ziti_version = ziti.ziti_get_version
_ziti_version.restype = ctypes.POINTER(_Ver)

_ziti_lasterr = ziti.Ziti_last_error

_ziti_errorstr = ziti.ziti_errorstr
_ziti_errorstr.argtypes = [ctypes.c_int]
_ziti_errorstr.restype = ctypes.c_char_p

_load_ctx = ziti.Ziti_load_context
_load_ctx.argtypes = [ctypes.POINTER(ctypes.c_char), ]
_load_ctx.restype = ctypes.c_void_p

_ziti_socket = ziti.Ziti_socket
_ziti_socket.argtypes = [ctypes.c_int]
_ziti_socket.restype = ctypes.c_int


_ziti_close = ziti.Ziti_close
_ziti_close.restype = None
_ziti_close.argtypes = [ctypes.c_int]


_ziti_connect = ziti.Ziti_connect
_ziti_connect.argtypes = [ctypes.c_int,     # socket fd
                          ctypes.c_void_p,  # zitt context
                          ctypes.c_char_p,  # service
                          ctypes.c_char_p   # terminator
                          ]

_ziti_connect_addr = ziti.Ziti_connect_addr
_ziti_connect_addr.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
_ziti_connect_addr.restype = ctypes.c_int

_ziti_bind = ziti.Ziti_bind
_ziti_bind.argtypes = [ctypes.c_int,     # socket fd
                       ctypes.c_void_p,  # ziti context
                       ctypes.c_char_p,  # service
                       ctypes.c_char_p   # terminator
                       ]

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

_ziti_resolve = ziti.Ziti_resolve
_ziti_resolve.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.POINTER(_AddrInfo),
    ctypes.c_void_p
]


def free_win32(_):
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
            raise Exception(err, msg)

        if err in [socket.EWOULDBLOCK, socket.EAGAIN]:
            raise BlockingIOError()

        msg = os.strerror(err)
        raise OSError(err, msg)


def init():
    ziti.Ziti_lib_init()


def ziti_socket(type):
    fd = _ziti_socket(type)
    return fd


def ziti_close(fd):
    if fd:
        _ziti_close(fd)


def shutdown():
    ziti.Ziti_lib_shutdown()


def load(path):
    init()
    b_obj = bytes(path, encoding="utf-8")
    return _load_ctx(b_obj)


def connect(fd, ztx, service: str, terminator: Optional[str] = None):
    srv = bytes(service, encoding='utf-8')
    terminator_b = None
    if terminator:
        terminator_b = bytes(terminator, encoding='utf-8')
    check_error(_ziti_connect(fd, ztx, srv, terminator_b))


def connect_addr(fd, addr: Tuple[str, int]):
    host = bytes(addr[0], encoding='utf-8')
    port = addr[1]
    check_error(_ziti_connect_addr(fd, host, port))


def bind(fd, ztx, service: str, terminator: Optional[str] = None):
    srv = bytes(service, encoding='utf-8')
    terminator_b = None
    if terminator:
        terminator_b = bytes(terminator, encoding='utf-8')
    check_error(_ziti_bind(fd, ztx, srv, terminator_b))


def listen(fd, backlog):
    check_error(_ziti_listen(fd, backlog))


def accept(fd):
    b = ctypes.create_string_buffer(128)
    clt = _ziti_accept(fd, b, 128)
    if clt < 0:
        check_error(clt)
    return clt, (bytes(b.value).decode('utf-8'), 0)


def enroll(jwt, key=None, cert=None):
    """
    Enroll Ziti Identity
    :param jwt: (required) enrollment token,
        can be either name of the token file or a string containing JWT
    :param key: private key to use for enrollment
        (required for 3rd party CA enrollment, otherwise optional,
        new key is generated if None)
    :param cert: certificate to use for enrollment
        (required for 3rd party CA enrollment)
    :return: string containing Ziti Identity in JSON format
    """
    init()
    try:
        with open(jwt, 'rb') as jwt_f:
            jwtc = bytes(jwt_f.read())
    except:
        jwtc = bytes(jwt, 'utf-8')

    id_json = ctypes.c_char_p()
    id_json_len = ctypes.c_size_t()

    keyb = None if key is None else bytes(key, 'utf-8')
    certb = None if cert is None else bytes(cert, 'utf-8')

    retcode = _ziti_enroll(jwtc, keyb, certb,
                           ctypes.byref(id_json),
                           ctypes.byref(id_json_len))
    if retcode != 0:
        raise RuntimeError(errorstr(retcode))
    try:
        return id_json.value.decode()
    finally:
        _free(id_json)


def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    # pylint: disable=redefined-builtin
    if not isinstance(host, bytes):
        host = bytes(str(host), 'utf-8')
    if not isinstance(port, bytes):
        port = bytes(str(port), 'utf-8')

    hints = _AddrInfo(ai_family=family, ai_socktype=type, ai_protocol=proto, ai_flags=flags)
    addr_p = ctypes.c_void_p()
    rc = _ziti_resolve(host, port, hints, ctypes.byref(addr_p))

    if rc != 0:
        return None

    addr_p = addr_p.value
    result = []
    while addr_p:
        addr = _AddrInfo.from_address(addr_p)
        addr_in = addr.get_addr()
        try:
            af = socket.AddressFamily(addr.ai_family)
        except:
            af = addr.ai_family
        try:
            t = socket.SocketKind(addr.ai_socktype)
        except:
            t = addr.ai_socktype

        a = (af, t, addr.ai_protocol, addr.get_canonname(), (addr_in.ip(), addr_in.port))
        result.append(a)
        addr_p = addr.ai_next

    return result
