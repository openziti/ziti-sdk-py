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
from os.path import isdir, isfile

from . import zitilib, zitisock


class ZitiContext:
    def __init__(self, ctx):
        if not isinstance(ctx, int):
            raise TypeError("ctx is not a valid python void pointer type")
        self._ctx = ctx

    def connect(self, addr):
        fd = zitilib.ziti_socket(socket.SOCK_STREAM)
        if isinstance(addr, str):
            zitilib.connect(fd, self._ctx, addr)
        elif isinstance(addr, tuple):
            zitilib.connect_addr(fd, addr)
        else:
            raise TypeError(f'unsupported address {addr}')
        return socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0, fd)

    def bind(self, service, sock=None):
        if sock is None:
            sock = zitisock.ZitiSocket(type=socket.SOCK_STREAM)
        zitilib.bind(sock.fileno(), self._ctx, service)
        return sock

    @classmethod
    def from_path(cls, path):
        if not isinstance(path, str):
            raise TypeError("path must be a string")
        if not (isfile(path) or isdir(path)):
            raise ValueError(f"{path} is not a valid path")
        return cls(zitilib.load(path))


def load_identity(path) -> ZitiContext:
    return ZitiContext.from_path(path)


def get_context(ztx) -> ZitiContext:
    if isinstance(ztx, ZitiContext):
        return ztx
    if isinstance(ztx, str):
        return ZitiContext.from_path(ztx)
    raise TypeError(f'{ztx} is not a ZitiContext or str instance')
