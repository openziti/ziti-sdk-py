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
from socket import getaddrinfo as PyGetaddrinfo
from socket import socket as PySocket
from typing import Tuple, Union

from . import context, zitilib


def process_bindings(orig):
    """normalize binding addresses"""
    bindings = {}

    if orig is not None:
        for k in orig:
            host = ''
            port = 0
            val = orig[k]
            if isinstance(k, tuple):
                host, port = k
            elif isinstance(k, str):
                l = k.split(':')
                if len(l) == 1:
                    port = l[0]
                else:
                    host, port = l
            elif isinstance(k, int):
                port = k

            host = '0.0.0.0' if host == '' else host
            bindings[(host, int(port))] = val

    return bindings


class ZitiSocket(PySocket):
    # pylint: disable=redefined-builtin
    def __init__(self, family=-1, type=-1, proto=-1, fileno=None, opts=None):
        zitilib.init()
        if opts is None:
            opts = {}
        self._ziti_bindings = process_bindings(opts.get('bindings'))
        self._bind_address = None
        self._ziti_opts = opts
        self._ziti_af = family
        self._ziti_type = type
        self._ziti_proto = proto
        if fileno:
            super().__init__(family, type, proto, fileno)
            return

        if type == -1:
            type = socket.SOCK_STREAM

        self._zitifd = zitilib.ziti_socket(type)
        super().__init__(family, type, proto, self._zitifd)

    def connect(self, addr) -> None:
        if self._zitifd is None:
            pass
        if isinstance(addr, tuple):
            self._ziti_peer = addr
            try:
                zitilib.connect_addr(self._zitifd, addr)
            except:
                PySocket.close(self)
                self._zitifd = None
                PySocket.__init__(self, self._ziti_af, self._ziti_type, self._ziti_proto)
                PySocket.connect(self, addr)

    def close(self) -> None:
        try:
            zitifd = getattr(self, '_zitifd')
        except AttributeError:
            super().close()
        else:
            zitilib.ziti_close(zitifd)

    def bind(self, addr) -> None:
        self._bind_address = addr
        h, p = addr
        cfg = self._ziti_bindings.get((h, int(p)))
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

    def getpeername(self):
        if hasattr(self, '_ziti_peer'):
            return self._ziti_peer
        else:
            return PySocket.getpeername(self)

    def getsockname(self) -> Tuple['str', int]:
        # return this for now since frameworks expect something to be returned
        return '127.0.0.1', 0

    def listen(self, __backlog: int = 5) -> None:
        try:
            zitilib.listen(self._zitifd, __backlog)
        except:
            super().listen(__backlog)

    def accept(self):
        fd, peer = zitilib.accept(self.fileno())
        return ZitiSocket(family=self._ziti_af, type=self._ziti_type, fileno=fd), peer

    def setsockopt(self, __level: int, __optname: int, __value: Union[int, bytes]) -> None:
        try:
            PySocket.setsockopt(self, __level, __optname, __value)
        except:
            pass


def create_ziti_connection(address, timeout=None,
                           source_address=None, *, all_errors=False):
    sock = ZitiSocket(socket.SOCK_STREAM)
    sock.connect(address)
    return sock


def ziti_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    # pylint: disable=redefined-builtin
    addrs = zitilib.getaddrinfo(host, port, family, type, proto, flags)
    if addrs is None:
        addrs = PyGetaddrinfo(host, port, family, type, proto, flags)
    return addrs
