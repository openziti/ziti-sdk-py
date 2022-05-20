#  Copyright (c)  NetFoundry Inc.
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

import socket as sock
from os import getenv
from . import zitilib, context, zitisock


_ziti_identities = filter(lambda p: p != '',
                          map(lambda s: s.strip(),
                              (getenv('ZITI_IDENTITIES') or "").split(';')))

_id_map = dict()

zitilib.init()

enroll = zitilib.enroll
version = zitilib.version
shutdown = zitilib.shutdown
load = context.load_identity
socket = zitisock.ZitiSocket

for id in _ziti_identities:
    if id != '':
        load(id)

_patch_methods = dict(
    create_connection = zitisock.create_ziti_connection,
    getaddrinfo = zitisock.ziti_getaddrinfo
)


class monkeypatch(object):
    def __init__(self):
        self.orig_socket = sock.socket
        sock.socket = zitisock.ZitiSocket
        self.orig_methods = dict((m, sock.__dict__[m]) for m in _patch_methods)
        for m in _patch_methods:
            sock.__dict__[m] = _patch_methods[m]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for m in self.orig_methods:
            sock.__dict__[m] = self.orig_methods[m]


from . import _version
__version__ = _version.get_versions()['version']
del _version
