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
from socket import socket as PySocket
from typing import Tuple

from . import zitilib


class ZitiSocket(PySocket):
    # pylint: disable=redefined-builtin
    def __init__(self, af=-1, type=-1, proto=-1, fileno=None):
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

        if isinstance(addr, Tuple):
            retcode = zitilib.connect(self._zitifd, addr)
            if retcode != 0:
                PySocket.close(self)
                self._zitifd = None
                PySocket.__init__(self, self._ziti_af, self._ziti_type,
                                  self._ziti_proto)
                PySocket.connect(self, addr)

    def setsockopt(self, __level, __optname, __value) -> None:
        try:
            PySocket.setsockopt(self, __level, __optname, __value)
        except:  # pylint: disable=bare-except
            pass


def create_ziti_connection(address, **_):
    sock = ZitiSocket(socket.SOCK_STREAM)
    sock.connect(address)
    return sock


def ziti_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    # pylint: disable=too-many-arguments, unused-argument
    # pylint: disable= redefined-builtin, protected-access, no-member
    return [(socket._intenum_converter(socket.AF_INET, socket.AddressFamily),
             socket._intenum_converter(type, socket.SocketKind),
             proto, '', (host, port))]
