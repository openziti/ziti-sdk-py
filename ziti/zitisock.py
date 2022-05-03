import socket
from typing import Tuple
from ziti import zitilib

py_socket = socket.socket

class ZitiSocket(py_socket):
    def __init__(self, af = -1, type = -1, proto = -1, fileno = None):
        self._ziti_af = af
        self._ziti_type = type
        self._ziti_proto = proto
        if fileno:
            py_socket.__init__(self, af, type, proto, fileno)
            return

        self._zitifd = zitilib.ziti_socket(type)
        py_socket.__init__(self, af, type, proto, self._zitifd)

    def connect(self, addr) -> None:
        if self._zitifd is None:
            pass

        if isinstance(addr, Tuple):
            rc = zitilib.connect(self._zitifd, addr)
            if rc != 0:
                py_socket.close(self)
                self._zitifd = None
                py_socket.__init__(self, self._ziti_af, self._ziti_type, self._ziti_proto)
                py_socket.connect(self, addr)

    def setsockopt(self, __level: int, __optname: int, __value: int | bytes) -> None:
        try:
            py_socket.setsockopt(self, __level, __optname, __value)
        except:
            pass


def create_ziti_connection(address,
                      timeout= socket._GLOBAL_DEFAULT_TIMEOUT,
                      source_address=None):
    s = ZitiSocket(socket.SOCK_STREAM)
    s.connect(address)
    return s


def ziti_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    addrlist = []
    addr = (
        socket._intenum_converter(socket.AF_INET, socket.AddressFamily),
        socket._intenum_converter(type, socket.SocketKind),
        proto, '', (host,port))

    addrlist.append(addr)
    return addrlist
