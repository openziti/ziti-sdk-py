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
