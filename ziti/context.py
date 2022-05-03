import socket
from ziti import zitilib

class ZitiContext:
    def __init__(self, ctx_p):
        self._ctx = ctx_p

    def connect(self, addr):
        fd = zitilib.ziti_socket(socket.SOCK_STREAM)
        service = bytes(addr, encoding = "utf-8")
        zitilib.ziti_connect(fd, self._ctx, service)
        return socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0, fd)


def load_identity(path) -> ZitiContext:
    return ZitiContext(zitilib.load(path))
