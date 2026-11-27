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

# pylint: disable=no-member

import ctypes
import enum
import errno
import os
import platform
import socket
import time
from typing import Callable, Optional, Tuple

_mod_path = os.path.dirname(__file__)
osname = platform.system().lower()

if osname == 'linux':
    LIBNAME = 'libziti.so'
elif osname == 'darwin':
    LIBNAME = 'libziti.dylib'
elif osname == 'windows':
    LIBNAME = 'ziti.dll'
else:
    raise ImportError("could not load ziti shared library")

zitilib_path = _mod_path + f'/lib/{LIBNAME}'
ziti = ctypes.CDLL(zitilib_path, use_errno=True)

last_error = ctypes.get_errno
if osname == 'windows':
    ws2lib = ctypes.WinDLL("ws2_32", use_last_error=True)
    ws2lib.WSAGetLastError.restype = ctypes.c_int
    last_error = ws2lib.WSAGetLastError


class _Ver(ctypes.Structure):
    _fields_ = [('version', ctypes.c_char_p), ('revision', ctypes.c_char_p)]

    def __repr__(self):
        return f'({self.version}, {self.revision})'


class SockAddrIn(ctypes.Structure):
    """
    maps struct sockaddr_in

    NOTE:
    -----
    On Linux/Win32 the first two bytes are address family as short,
    on Darwin the first two bytes.
    """
    _fields_ = [
        ('_family', ctypes.c_uint8 * 2),
        ('_port', ctypes.c_uint16),
        ('_addr', ctypes.c_uint8 * 4)
    ]

    def ip(self):
        return '.'.join(str(o) for o in self._addr)

    def af(self):
        fam = self._family[0]
        if osname == 'darwin':
            fam = self._family[1]
        return socket.AddressFamily(fam)

    @property
    def port(self):
        return socket.ntohs(self._port)
    def __repr__(self):
        return f'{self.af().name}:{self.ip()}:{self.port}'


class _AddrInfo(ctypes.Structure):
    """
    int ai_flags;              /* Input flags. */
    int ai_family;             /* Protocol family for socket. */
    int ai_socktype;           /* Socket type. */
    int ai_protocol;           /* Protocol for socket. */
    socklen_t ai_addrlen;      /* Length of socket address. */
    struct sockaddr *ai_addr;  /* Socket address for socket. */
    char *ai_canonname;        /* Canonical name for service location. */
    struct addrinfo *ai_next;  /* Pointer to next in list. */

    NOTE:
    -----
    The order of ai_addr and ai_canonname is switched on
    Darwin and Windows compared to Linux.
    """
    _fields_ = [
        ('ai_flags', ctypes.c_int),
        ('ai_family', ctypes.c_int),
        ('ai_socktype', ctypes.c_int),
        ('ai_protocol', ctypes.c_int),
        ('ai_addrlen', ctypes.c_int32),
        ('ai_p1', ctypes.c_void_p),
        ('ai_p2', ctypes.c_void_p),
        ('ai_next', ctypes.c_void_p)
    ]

    def get_addr(self):
        addr_p = self.ai_p2
        if osname == 'linux':
            addr_p = self.ai_p1
        if addr_p is None:
            return None
        return SockAddrIn.from_address(addr_p)

    def get_canonname(self):
        p = self.ai_p1
        if osname == 'linux':
            p = self.ai_p2
        if p is None:
            return None
        return str(ctypes.cast(p, ctypes.c_char_p))

    def __repr__(self):
        return '|'.join((x[0] + '=' + str(getattr(self, x[0])))
                        for x in _AddrInfo._fields_)


_ziti_version = ziti.ziti_get_version
_ziti_version.restype = ctypes.POINTER(_Ver)

_ziti_lasterr = ziti.Ziti_last_error

_ziti_errorstr = ziti.ziti_errorstr
_ziti_errorstr.argtypes = [ctypes.c_int]
_ziti_errorstr.restype = ctypes.c_char_p

_load_ctx = ziti.Ziti_load_context_with_timeout
_load_ctx.argtypes = [
    ctypes.POINTER(ctypes.c_int32), # ziti context handle
    ctypes.POINTER(ctypes.c_char), # ziti identity path or json
    ctypes.c_int, # ziti timeout in ms
]
_load_ctx.restype = ctypes.c_int

_get_signers = ziti.Ziti_get_ext_signers
_get_signers.argtypes = [
    ctypes.c_int32, # ziti context handle
]
_get_signers.restype = ctypes.POINTER(ctypes.c_char_p)

_login_external = ziti.Ziti_login_external
_login_external.argtypes = [
    ctypes.c_int32, # ziti context handle
    ctypes.c_char_p, # external signer name
]
_login_external.restype = ctypes.c_char_p


_login_totp = ziti.Ziti_login_totp
_login_totp.argtypes = [
    ctypes.c_int32, # ziti context handle
    ctypes.c_char_p, # totp code
]
_login_totp.restype = ctypes.c_int


_wait_for_auth = ziti.Ziti_wait_for_auth
_wait_for_auth.argtypes = [
    ctypes.c_int32,  # ziti context handle
    ctypes.c_int,  # timeout in ms, 0 is no timeout
]
_wait_for_auth.restype = ctypes.c_int

_login_with_token = ziti.Ziti_login_with_token
_login_with_token.argtypes = [
    ctypes.c_int32,  # ziti context handle
    ctypes.c_char_p,  # external JWT
]
_login_with_token.restype = ctypes.c_int

_ziti_socket = ziti.Ziti_socket
_ziti_socket.argtypes = [ctypes.c_int]
_ziti_socket.restype = ctypes.c_int


_ziti_close = ziti.Ziti_close
_ziti_close.restype = None
_ziti_close.argtypes = [ctypes.c_int]


_ziti_connect = ziti.Ziti_connect
_ziti_connect.argtypes = [ctypes.c_int,     # socket fd
                          ctypes.c_void_p,  # zitt context
                          ctypes.c_char_p,  # service
                          ctypes.c_char_p   # terminator
                          ]

_ziti_connect_addr = ziti.Ziti_connect_addr
_ziti_connect_addr.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
_ziti_connect_addr.restype = ctypes.c_int

_ziti_bind = ziti.Ziti_bind
_ziti_bind.argtypes = [ctypes.c_int,     # socket fd
                       ctypes.c_void_p,  # ziti context
                       ctypes.c_char_p,  # service
                       ctypes.c_char_p   # terminator
                       ]

_ziti_listen = ziti.Ziti_listen
_ziti_listen.argtypes = [ctypes.c_int, ctypes.c_int]

_ziti_accept = ziti.Ziti_accept
_ziti_accept.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]

_ziti_enroll = ziti.Ziti_enroll_identity
_ziti_enroll.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.POINTER(ctypes.c_size_t)
]
_ziti_enroll.restype = ctypes.c_int

_enroll_with_idp = ziti.Ziti_enroll_with_idp
_enroll_with_idp.argtypes = [
    ctypes.c_char_p,  # controller url or network JWT
    ctypes.c_int,  # ziti_enroll_mode
    ctypes.c_char_p,  # token or ext-jwt-signer name, NULL for the first signer
    ctypes.POINTER(ctypes.c_uint32),  # (output) handle of the enrollment that waits for a login
    ctypes.POINTER(ctypes.c_char_p),  # (output) identity json
    ctypes.POINTER(ctypes.c_ulong),  # (output) length of the identity json
]
_enroll_with_idp.restype = ctypes.c_int

_enroll_login_url = ziti.Ziti_enroll_login_url
_enroll_login_url.argtypes = [ctypes.c_uint32]  # handle of the pending enrollment
_enroll_login_url.restype = ctypes.c_char_p  # belongs to the pending enrollment: not freed

_enroll_continue = ziti.Ziti_enroll_continue
_enroll_continue.argtypes = [
    ctypes.c_uint32,  # handle of the pending enrollment
    ctypes.c_int,  # how long to wait for the login in ms, 0 is for ever
    ctypes.POINTER(ctypes.c_char_p),  # (output) identity json
    ctypes.POINTER(ctypes.c_ulong),  # (output) length of the identity json
]
_enroll_continue.restype = ctypes.c_int

_enroll_cancel = ziti.Ziti_enroll_cancel
_enroll_cancel.argtypes = [ctypes.c_uint32]  # handle of the pending enrollment
_enroll_cancel.restype = ctypes.c_int

_ziti_resolve = ziti.Ziti_resolve
_ziti_resolve.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.POINTER(_AddrInfo),
    ctypes.c_void_p
]


def free_win32(_):
    pass


if osname != 'windows':
    _free = ziti.free
    _free.argtypes = [ctypes.c_void_p]
else:
    _free = free_win32


def version():
    ver = _ziti_version().contents
    return ver


def errorstr(code):
    msg = _ziti_errorstr(code)
    return msg.decode()


def check_error(code):
    if code != 0:
        err_no = last_error()
        err = _ziti_lasterr()

        if err_no in [socket.EWOULDBLOCK, socket.EAGAIN, errno.EINPROGRESS]:
            raise BlockingIOError()
        if err_no == errno.EINTR:
            raise InterruptedError()

        if err < 0:
            msg = _ziti_errorstr(err).decode(encoding='utf-8')
            raise Exception(err, msg)

        if err_no != 0:
            msg = os.strerror(err_no)
            raise OSError(err_no, msg)


def init():
    ziti.Ziti_lib_init()


def ziti_socket(type):
    fd = _ziti_socket(type)
    return fd


def ziti_close(fd):
    if fd:
        _ziti_close(fd)


def shutdown():
    ziti.Ziti_lib_shutdown()


def load(path, timeout=0) -> tuple[int, int]:
    init()
    b_obj = bytes(path, encoding="utf-8")
    hp = ctypes.c_int32()

    err = _load_ctx(ctypes.pointer(hp), b_obj, ctypes.c_int(timeout))
    return hp.value, err

def login_external(ziti_ctx: int, name: str) -> str:
    init()
    name_b = bytes(name, encoding='utf-8')
    url = _login_external(ziti_ctx, name_b)
    return url.decode('utf-8')

def list_external_signers(ziti_ctx: int) -> list[str]:
    init()
    signers_p = _get_signers(ziti_ctx)

    signers = []
    if not signers_p:
        return signers

    idx = 0
    while signers_p[idx]:
        signers.append(signers_p[idx].decode('utf-8'))
        idx += 1

    return signers

def login_totp(ziti_ctx: int, totp: str) -> int:
    init()
    totp_b = bytes(totp, encoding='utf-8')
    return _login_totp(ziti_ctx, totp_b)

def login_with_token(ziti_ctx: int, token: str) -> int:
    init()
    return _login_with_token(ziti_ctx, bytes(token, encoding='utf-8'))

def wait_for_auth(ziti_ctx: int, timeout:int) -> int:
    init()
    return _wait_for_auth(ziti_ctx, timeout * 1000)

def connect(fd, ztx, service: str, terminator: Optional[str] = None):
    srv = bytes(service, encoding='utf-8')
    terminator_b = None
    if terminator:
        terminator_b = bytes(terminator, encoding='utf-8')
    check_error(_ziti_connect(fd, ztx, srv, terminator_b))


def connect_addr(fd, addr: Tuple[str, int]):
    host = bytes(addr[0], encoding='utf-8')
    port = addr[1]
    check_error(_ziti_connect_addr(fd, host, port))


def bind(fd, ztx, service: str, terminator: Optional[str] = None):
    srv = bytes(service, encoding='utf-8')
    terminator_b = None
    if terminator:
        terminator_b = bytes(terminator, encoding='utf-8')
    check_error(_ziti_bind(fd, ztx, srv, terminator_b))


def listen(fd, backlog):
    check_error(_ziti_listen(fd, backlog))


def accept(fd):
    b = ctypes.create_string_buffer(128)
    clt = _ziti_accept(fd, b, 128)
    if clt < 0:
        check_error(clt)
    return clt, (bytes(b.value).decode('utf-8'), 0)


def enroll(jwt, key=None, cert=None):
    """
    Enroll Ziti Identity
    :param jwt: (required) enrollment token,
        can be either name of the token file or a string containing JWT
    :param key: private key to use for enrollment
        (required for 3rd party CA enrollment, otherwise optional,
        new key is generated if None)
    :param cert: certificate to use for enrollment
        (required for 3rd party CA enrollment)
    :return: string containing Ziti Identity in JSON format
    """
    init()
    try:
        with open(jwt, 'rb') as jwt_f:
            jwtc = bytes(jwt_f.read())
    except:
        jwtc = bytes(jwt, 'utf-8')

    id_json = ctypes.c_char_p()
    id_json_len = ctypes.c_size_t()

    keyb = None if key is None else bytes(key, 'utf-8')
    certb = None if cert is None else bytes(cert, 'utf-8')

    retcode = _ziti_enroll(jwtc, keyb, certb,
                           ctypes.byref(id_json),
                           ctypes.byref(id_json_len))
    if retcode != 0:
        raise RuntimeError(errorstr(retcode))
    try:
        return id_json.value.decode()
    finally:
        _free(id_json)


class EnrollMode(enum.IntEnum):
    """What the controller does for a token of an ext-jwt-signer (``ziti_enroll_mode``)."""
    #: the identity exists already: the result is the bootstrap config (controller address and CA, no cert or key)
    NONE = 0
    #: the app generates a key and a CSR, the controller signs it for the token: the identity has a cert and key
    CERT = 1
    #: the controller creates the identity: it has no cert, and the token is its login
    TOKEN = 2


_ZITI_TIMEOUT = -20
_EXTERNAL_LOGIN_REQUIRED = -39

# the redirect uri of a login with an external provider is always localhost:20314 (``auth_cb_port`` in ziti-sdk-c)
_LOGIN_PORT = 20314


def _wait_for_login_port_to_free(timeout: float = 3.0) -> None:
    """Return when nothing listens on the SDK's login port, or after ``timeout`` seconds.

    The listener of a login that was cancelled does not go away at once: its worker notices the cancel up to a
    second later and closes the socket then (ziti-sdk-c 1.22.1). A login that starts before that binds the same
    port next to it (the SDK sets SO_REUSEADDR and SO_REUSEPORT), and the redirect of the new login can be handed
    to the old listener, which drops it: the user's browser gets a refused or reset connection, and the login
    never completes.

    A connection also wakes the dying listener, so asking whether it is still there makes it go sooner. This is
    only for a listener of the process's own cancelled enrollment: one login can be pending per machine.

    A refused connection can also mean a listener whose queue is full of these very connections (macOS). The
    dying listener stops at the first of them, and closes its socket a moment later, long before the next login
    has a redirect to deliver.

    Each attempt gets all the time that is left, because a closed loopback port is refused slowly on Windows (the
    stack retries the SYN first): an attempt that gave up sooner would see only silence, and this would go on
    until ``timeout`` even when nothing listens.
    """
    deadline = time.monotonic() + timeout
    while (left := deadline - time.monotonic()) > 0:
        try:
            socket.create_connection(("::1", _LOGIN_PORT), timeout=left).close()
        except OSError:
            # refused: nothing listens (or there is no IPv6 loopback, and the SDK has no listener either).
            # A timeout is an OSError too, and it is the end of the time to wait: the next login says what is wrong.
            return
        time.sleep(0.05)


def _identity_json(id_json: ctypes.c_char_p) -> str:
    """The identity json the native library handed out, which the caller has to free."""
    try:
        return id_json.value.decode()
    finally:
        _free(id_json)


def enroll_with_idp(controller: str, mode: EnrollMode | int, idp: str | None = None, *,
                    on_login_url: Callable[[str], None] | None = None,
                    timeout: float | None = 300.0) -> str:
    """
    Enroll a Ziti identity with an external identity provider (IdP): a controller trusts an ext-jwt-signer and,
    for a token of the signer, creates the identity (needs controller 2.0 or later).

    :param controller: controller URL, or the network JWT. A URL needs the TLS certificate of the controller
        to be trusted by the OS; with the network JWT, which is the controller's trust anchor, a controller with
        a private CA is fine.
    :param mode: :class:`EnrollMode`. ``NONE`` needs no ``idp`` and returns the bootstrap config.
    :param idp: a token of the signer (a JWT, e.g. the OIDC token of a CI job), which is handed to the controller
        as it is, or the name of an ext-jwt-signer to log in with in a browser, or ``None`` to log in with the
        first signer that offers the mode.
    :param on_login_url: called with the url that the user has to open, when the enrollment needs a login with a
        signer. The enrollment then waits for the user to finish the login (the SDK listens for its redirect on
        a fixed local port, so one login can be pending at a time). Without it, an enrollment that needs a
        login fails.
    :param timeout: how long to wait for the login in seconds, ``None`` to wait for ever
    :return: string containing the Ziti Identity in JSON format. Enrolled to a token, it has no cert or key:
        load it, and then ``ZitiContext.login_with_token()`` or ``ZitiContext.login_external()``.
    :raises TimeoutError: the user did not log in within ``timeout``
    :raises RuntimeError: the enrollment failed, or it needs a login and there is no ``on_login_url``
    """
    if not isinstance(controller, str):
        raise TypeError("controller must be a string")
    if not controller:
        raise ValueError("controller must be a controller url or a network JWT")
    mode = EnrollMode(mode)
    if idp is not None and not isinstance(idp, str):
        raise TypeError("idp must be a string or None")
    init()

    pending = ctypes.c_uint32()
    id_json = ctypes.c_char_p()
    id_json_len = ctypes.c_ulong()
    retcode = _enroll_with_idp(controller.encode(), int(mode), None if idp is None else idp.encode(),
                               ctypes.byref(pending), ctypes.byref(id_json), ctypes.byref(id_json_len))
    if retcode == _EXTERNAL_LOGIN_REQUIRED:
        return _finish_enroll_login(pending.value, on_login_url, timeout)
    if retcode != 0:
        raise RuntimeError(errorstr(retcode))
    return _identity_json(id_json)


def _finish_enroll_login(pending: int, on_login_url, timeout) -> str:
    """Hand out the login url of a pending enrollment, wait for the user and get the identity.

    There is one pending enrollment at a time: whatever goes wrong here, it is abandoned, and the next one can
    start when this returns. That takes more than ``Ziti_enroll_cancel``, which frees the pending slot at once but
    leaves the login listener up for as long as a second (see ``_wait_for_login_port_to_free``).
    """
    over = False  # any result of ``Ziti_enroll_continue`` but a timeout releases the handle
    try:
        if on_login_url is None:
            raise RuntimeError("the enrollment needs a login in a browser: pass on_login_url to get its url")
        url = _enroll_login_url(pending)
        if url is None:
            raise RuntimeError("the pending enrollment has no login url")
        on_login_url(url.decode())

        id_json = ctypes.c_char_p()
        id_json_len = ctypes.c_ulong()
        wait_ms = 0 if timeout is None else max(1, int(timeout * 1000))  # 0 is for ever
        retcode = _enroll_continue(pending, wait_ms, ctypes.byref(id_json), ctypes.byref(id_json_len))
        if retcode == _ZITI_TIMEOUT:
            raise TimeoutError(f"the login was not completed within {timeout}s")
        over = True
        if retcode != 0:
            raise RuntimeError(errorstr(retcode))
        return _identity_json(id_json)
    finally:
        if not over:
            _enroll_cancel(pending)
            _wait_for_login_port_to_free()


def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    # pylint: disable=redefined-builtin
    if not isinstance(host, bytes):
        host = bytes(str(host), 'utf-8')
    if not isinstance(port, bytes):
        port = bytes(str(port), 'utf-8')

    hints = _AddrInfo(ai_family=family, ai_socktype=type, ai_protocol=proto, ai_flags=flags)
    addr_p = ctypes.c_void_p()
    rc = _ziti_resolve(host, port, hints, ctypes.byref(addr_p))

    if rc != 0:
        return None

    addr_p = addr_p.value
    result = []
    while addr_p:
        addr = _AddrInfo.from_address(addr_p)
        addr_in = addr.get_addr()
        try:
            af = socket.AddressFamily(addr.ai_family)
        except:
            af = addr.ai_family
        try:
            t = socket.SocketKind(addr.ai_socktype)
        except:
            t = addr.ai_socktype

        a = (af, t, addr.ai_protocol, addr.get_canonname(), (addr_in.ip(), addr_in.port))
        result.append(a)
        addr_p = addr.ai_next

    return result
