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
from socket import getaddrinfo as PyGetaddrinfo
from socket import socket as PySocket
from typing import Tuple, Union

from . import context, zitilib


class ZitiSocket(PySocket):
    # pylint: disable=redefined-builtin
    def __init__(self, af=-1, type=-1, proto=-1, fileno=None, opts=None):
        zitilib.init()
        if opts is None:
            opts = {}
        if opts.get('bindings') is None:
            opts['bindings'] = {}
        self._bind_address = None
        self._ziti_opts = opts
        self._ziti_af = af
        self._ziti_type = type
        self._ziti_proto = proto
        if fileno:
            super().__init__(af, type, proto, fileno)
            return

        if type == -1:
            type = socket.SOCK_STREAM

        self._zitifd = zitilib.ziti_socket(type)
        super().__init__(af, type, proto, self._zitifd)

    def connect(self, addr) -> None:
        if self._zitifd is None:
            pass
        if isinstance(addr, tuple):
            try:
                zitilib.connect_addr(self._zitifd, addr)
            except:
                PySocket.close(self)
                self._zitifd = None
                PySocket.__init__(self, self._ziti_af, self._ziti_type, self._ziti_proto)
                PySocket.connect(self, addr)

    def close(self) -> None:
        zitifd = getattr(self, '_zitifd')
        if zitifd:
            zitilib.ziti_close(zitifd)
        else:
            super().close()

    def bind(self, addr) -> None:
        self._bind_address = addr
        bindings = self._ziti_opts['bindings']
        cfg = bindings.get(addr)
        if cfg is not None:
            ztx = context.get_context(cfg['ztx'])
            service = cfg['service']
            terminator = None
            if isinstance(service, tuple):
                service, terminator = service
            ztx.bind(service=service, terminator=terminator, sock=self)
        else:
            PySocket.close(self)
            self._zitifd = None
            PySocket.__init__(self, self._ziti_af, self._ziti_type, self._ziti_proto)
            PySocket.bind(self, addr)

    def getsockname(self) -> Tuple['str', int]:
        # return this for now since frameworks expect something to be returned
        return ('127.0.0.1', 0)

    def listen(self, __backlog: int = 5) -> None:
        try:
            zitilib.listen(self._zitifd, __backlog)
        except:
            super().listen(__backlog)

    def accept(self):
        fd, peer = zitilib.accept(self.fileno())
        return ZitiSocket(af=self._ziti_af, type=self._ziti_type, fileno=fd), peer

    def setsockopt(self, __level: int, __optname: int, __value: Union[int, bytes]) -> None:
        try:
            PySocket.setsockopt(self, __level, __optname, __value)
        except:
            pass


def create_ziti_connection(address, **_):
    sock = ZitiSocket(socket.SOCK_STREAM)
    sock.connect(address)
    return sock


def ziti_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    # pylint: disable=redefined-builtin
    addrs = zitilib.getaddrinfo(host, port, family, type, proto, flags)
    if addrs is None:
        addrs = PyGetaddrinfo(host, port, family, type, proto, flags)
    return addrs
