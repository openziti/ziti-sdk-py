import ctypes
import encodings
import os
from typing import Tuple

_mod_path = os.path.dirname(__file__)
print (_mod_path)
ziti = ctypes.CDLL(_mod_path + '/libziti.so')


class _Ver(ctypes.Structure):
    _fields_ = [('version', ctypes.c_char_p), ('revision', ctypes.c_char_p)]

    def __repr__(self):
        return '({0}, {1})'.format(self.version, self.revision)


_ziti_version = ziti.ziti_get_version
_ziti_version.restype = ctypes.POINTER(_Ver)

_load_ctx = ziti.Ziti_load_context
_load_ctx.argtypes = [ctypes.POINTER(ctypes.c_char), ]
_load_ctx.restype = ctypes.c_void_p

ziti_socket = ziti.Ziti_socket
ziti_socket.argtypes = [ctypes.c_int]
ziti_socket.restype = ctypes.c_int

ziti_connect = ziti.Ziti_connect
ziti_connect.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p]


_ziti_connect_addr = ziti.Ziti_connect_addr
_ziti_connect_addr.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
_ziti_connect_addr.restype = ctypes.c_int


def version():
    ver = _ziti_version().contents
    return ver


def init():
    ziti.Ziti_lib_init()


def shutdown():
    ziti.Ziti_lib_shutdown()


def load(path):
    b = bytes(path, encoding = "utf-8")
    return _load_ctx(b)


def connect(fd, addr: Tuple[str, int]):
    host = bytes(addr[0], encoding = 'utf-8')
    port = addr[1]
    return _ziti_connect_addr(fd, host, port)