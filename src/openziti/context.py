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

import socket
from os.path import isdir, isfile

from . import zitilib, zitisock


class ZitiContext:
    """
    Object representing a Ziti Identity.
    """
    def __init__(self, ctx):
        if not isinstance(ctx, int):
            raise TypeError("ctx is not a valid python void pointer type")
        self._ctx = ctx

    def connect(self, addr, terminator=None):
        """
        Connect to a Ziti service.
        Either service name or intercept address(host,port)
        could be used to connect to service.

        :param addr: service name (string) or
            service intercept address(tuple[host, port])
        :param terminator: specific terminator for the given service,
            ignored if [addr] is an intercept address
        :return: socket connected to the service
        """
        fd = zitilib.ziti_socket(socket.SOCK_STREAM)
        if isinstance(addr, str):
            zitilib.connect(fd, self._ctx, service=addr, terminator=terminator)
        elif isinstance(addr, tuple):
            zitilib.connect_addr(fd, addr)
        else:
            raise TypeError(f'unsupported address {addr}')
        return socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0, fd)

    def bind(self, service, terminator=None, sock=None):
        """
        Bind to a Ziti service and return server socket.

        :param service: service name to bind to
        :param terminator: (optional) bind with specific terminator
        :param sock: existing socket to bind
        :return: server socket ready for accept() call
        """
        if sock is None:
            sock = zitisock.ZitiSocket(type=socket.SOCK_STREAM)
        zitilib.bind(sock.fileno(), self._ctx, service, terminator)
        return sock

    @classmethod
    def from_path(cls, path):
        """
        Load Ziti Identity

        :param path: path to Ziti Identity file
        :return: ZitiContext representing given identity
        """
        if not isinstance(path, str):
            raise TypeError("path must be a string")
        if not (isfile(path) or isdir(path)):
            raise ValueError(f"{path} is not a valid path")
        return cls(zitilib.load(path))


def load_identity(path) -> ZitiContext:
    """
    Load Ziti Identity

    :param path: path to Ziti Identity file
    :return: Ziti Context object representing Ziti Identity
    """
    return ZitiContext.from_path(path)


def get_context(ztx) -> ZitiContext:
    if isinstance(ztx, ZitiContext):
        return ztx
    if isinstance(ztx, str):
        return ZitiContext.from_path(ztx)
    raise TypeError(f'{ztx} is not a ZitiContext or str instance')
