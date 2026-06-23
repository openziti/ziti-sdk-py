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
import asyncio
import logging
import socket

from asyncio import StreamWriter, StreamReader, StreamReaderProtocol
from os.path import isdir, isfile
from ssl import SSLContext

from . import zitilib, zitisock


class ZitiContext:
    EXTERNAL_LOGIN_REQUIRED = -39
    PARTIALLY_AUTHENTICATED = -31
    """
    Object representing a Ziti Identity.
    """
    def __init__(self, ctx):
        if not isinstance(ctx, int):
            raise TypeError("ctx is not a valid python void pointer type")
        self._ctx = ctx

    def connect(self, addr, terminator=None, timeout: float | None = None) -> socket.socket:
        """
        Connect to a Ziti service.
        Either service name or intercept address(host,port)
        could be used to connect to service.

        :param addr: service name (string) or
            service intercept address(tuple[host, port])
        :param terminator: specific terminator for the given service,
            ignored if [addr] is an intercept address
        :param timeout: socket timeout in seconds
        :return: socket connected to the service
        """
        fd = zitilib.ziti_socket(socket.SOCK_STREAM)
        s = socket.socket(family=socket.AF_UNSPEC, type=socket.SOCK_STREAM, fileno=fd)
        s.settimeout(timeout)
        if isinstance(addr, str):
            zitilib.connect(fd, self._ctx, service=addr, terminator=terminator)
        elif isinstance(addr, tuple):
            zitilib.connect_addr(fd, addr)
        else:
            s.close()
            raise TypeError(f'unsupported address {addr}')
        return s

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
    def from_path(cls, path, timeout=0) -> tuple["ZitiContext", int]:
        """
        Load Ziti Identity

        :param path: path to Ziti Identity file
        :param timeout: timeout in milliseconds for loading identity
        :return: ZitiContext representing given identity
        """
        if not isinstance(path, str):
            raise TypeError("path must be a string")
        if not (isfile(path) or isdir(path)):
            raise ValueError(f"{path} is not a valid path")
        zh, err = zitilib.load(path, timeout)
        if err != 0:
            logging.warning("Failed to load Ziti Identity from %s: %s", path, zitilib.errorstr(err))
        return cls(zh), err

    def get_external_signers(self):
        return zitilib.list_external_signers(self._ctx)

    def login_external(self, signer) -> str:
        if not isinstance(signer, str):
            raise TypeError("signer must be a string")
        return zitilib.login_external(self._ctx, signer)

    def login_totp(self, totp: str) -> None:
        code = zitilib.login_totp(self._ctx, totp)
        if code != 0:
            raise RuntimeError(f"Failed to login with TOTP: {zitilib.errorstr(code)}")

    def wait_for_auth(self, timeout=60):
        return zitilib.wait_for_auth(self._ctx, timeout)

    async def open_connection(
            self,
            service: str | None = None, terminator: str | None = None,
            host: str | None  = None, port: int | None = None,
            ssl: bool | None | SSLContext | None = None,
            server_hostname: str | None = None,
    ) -> tuple[StreamReader, StreamWriter]:
        """
        Open an async streaming connection to a Ziti service.

        Specify the target as either a service name or an intercept address — not both.

        :param service: Ziti service name to connect to.
        :param terminator: specific terminator for the service; requires ``service``.
        :param host: intercept hostname; must be paired with ``port``.
        :param port: intercept port; must be paired with ``host``.
        :param ssl: wrap the connection in TLS. Pass ``True`` to use default SSL
            context, or an :class:`ssl.SSLContext` for custom settings.
        :param server_hostname: SNI hostname for TLS verification. Defaults to
            ``host`` when connecting by intercept address. Required when using
            ``ssl`` with a service name (no ``host``).
        :returns: ``(reader, writer)`` — :class:`asyncio.StreamReader` and
            :class:`asyncio.StreamWriter` connected to the service.
        :raises ValueError: if the parameter combination is invalid (e.g.
            ``terminator`` without ``service``, ``host`` without ``port``,
            neither ``service`` nor ``host``/``port`` given, or ``ssl`` with a
            service name and no ``server_hostname``).
        """
        loop = asyncio.get_running_loop()

        if terminator and service is None:
            raise ValueError("terminator cannot be used without service")
        if service and (host or port):
            raise ValueError("service and host/port cannot be used together")
        if (host and port is None) or (host is None and port):
            raise ValueError("host and port(>0) must be specified together")
        if service is None and host is None:
            raise ValueError("one of service or (host, port) must be specified")

        if ssl and not server_hostname:
            if host:
                server_hostname = host
            else:
                raise ValueError("server_hostname is required for ssl connection without host")

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0, )
        s.setblocking(False)
        try:
            if service:
                zitilib.connect(s.fileno(), self._ctx, service, terminator)
            elif host and port:
                zitilib.connect_addr(s.fileno(), (host, port))
            else:
                s.close()
                raise ValueError("invalid connection parameters")
        except BlockingIOError:
            pass
        except:
            s.close()
            raise

        reader = StreamReader()
        protocol = StreamReaderProtocol(reader)
        transport, _ = await loop.create_connection(lambda: protocol, sock = s, ssl=ssl, server_hostname=server_hostname)
        writer = StreamWriter(transport=transport, protocol=protocol, reader=reader, loop=loop)
        return reader, writer


def load_identity(path, timeout=0) -> tuple[ZitiContext, int]:
    """
    Load Ziti Identity

    :param path: path to Ziti Identity file
    :param timeout: timeout in milliseconds for loading identity
    :return: Ziti Context object representing Ziti Identity
    """
    return ZitiContext.from_path(path, timeout)


def get_context(ztx, timeout=0) -> ZitiContext:
    if isinstance(ztx, ZitiContext):
        return ztx
    if isinstance(ztx, str):
        z, _ = ZitiContext.from_path(ztx, timeout)
        return z
    raise TypeError(f'{ztx} is not a ZitiContext or str instance')
