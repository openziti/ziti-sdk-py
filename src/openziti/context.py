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

from . import zitilib, zitisock


class ZitiContext:
    # pylint: disable=too-few-public-methods
    def __init__(self, ctx):
        ztx = ctx
        if isinstance(ctx, str):
            ztx = zitilib.load(ctx)
        self._ctx = ztx

    def connect(self, addr):
        # pylint: disable=invalid-name
        fd = zitilib.ziti_socket(socket.SOCK_STREAM)
        if addr is str:
            zitilib.connect(fd, self._ctx, addr)
        elif addr is tuple:
            zitilib.connect_addr(fd, addr)
        else:
            raise RuntimeError(f'unsupported address {addr}')
        return socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0, fd)

    def bind(self, service, sock=None):
        if sock is None:
            sock = zitisock.ZitiSocket(type=socket.SOCK_STREAM)
        zitilib.bind(sock.fileno(), self._ctx, service)
        return sock


def load_identity(path) -> ZitiContext:
    return ZitiContext(zitilib.load(path))


def get_context(ztx) -> ZitiContext:
    if isinstance(ztx, ZitiContext):
        return ztx
    if isinstance(ztx, str):
        return ZitiContext(ztx)
    raise RuntimeError(f'{ztx} is not a Ziti Context or a path')