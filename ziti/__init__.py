import os.path
from ziti import zitilib
from ziti import context
from ziti import zitisock
import socket

_ziti_identities = (os.getenv('ZITI_IDENTITIES') or "").split(';')
_id_map = dict()

zitilib.init()

version = zitilib.version
shutdown = zitilib.shutdown
load = context.load_identity

for id in _ziti_identities:
    if id != '':
        load(id)

_patch_methods = dict(
    create_connection = zitisock.create_ziti_connection,
    getaddrinfo = zitisock.ziti_getaddrinfo
)


class monkeypatch(object):
    def __init__(self):
        print('setting ziti overrides')
        self.orig_socket = socket.socket
        socket.socket = zitisock.ZitiSocket
        self.orig_methods = dict((m, socket.__dict__[m]) for m in _patch_methods)
        for m in _patch_methods:
            socket.__dict__[m] = _patch_methods[m]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for m in self.orig_methods:
            socket.__dict__[m] = self.orig_methods[m]
