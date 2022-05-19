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

import socket
from . import zitilib


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
