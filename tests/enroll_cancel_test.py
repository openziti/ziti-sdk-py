#  Copyright (c) 2026.  NetFoundry Inc
#
#  SPDX-License-Identifier: Apache-2.0
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

"""What ``enroll_with_idp`` does when it abandons an enrollment that waits for a login.

The SDK's login listener does not go away when the enrollment is cancelled: its worker notices the cancel up to a
second later (ziti-sdk-c 1.22.1, ``ext_accept`` in ``ext_oidc.c``). An enrollment that starts before that binds
the same port next to the dying listener, and the redirect of its login can be handed to the dying one, which
drops it. So ``enroll_with_idp`` waits for the port to be free after a cancel, and these tests pin that down
without depending on which of the two listeners the system picks: the native calls are replaced, and the port
is one of a socket of the test.
"""

import socket
import threading
import time

import pytest

from openziti import EnrollMode, zitilib

LOGIN_URL = b"https://idp.example.com/authorize"
INVALID_STATE = -22
TIMEOUT = -20
EXTERNAL_LOGIN_REQUIRED = -39


class Events(list):
    """What happened to the enrollment, in order; ``continue_result`` is what ``Ziti_enroll_continue`` answers."""
    continue_result = TIMEOUT


@pytest.fixture
def events(monkeypatch):
    """Replace the native calls of an enrollment that waits for a login."""
    events = Events()

    monkeypatch.setattr(zitilib, "_enroll_with_idp", lambda *args: EXTERNAL_LOGIN_REQUIRED)
    monkeypatch.setattr(zitilib, "_enroll_login_url", lambda handle: LOGIN_URL)
    monkeypatch.setattr(zitilib, "_enroll_continue",
                        lambda *args: events.append("continue") or events.continue_result)
    monkeypatch.setattr(zitilib, "_enroll_cancel", lambda handle: events.append("cancel") or 0)
    monkeypatch.setattr(zitilib, "_wait_for_login_port_to_free", lambda: events.append("wait"))
    return events


def enroll(**kwargs):
    return zitilib.enroll_with_idp("https://ctrl", EnrollMode.TOKEN, "signer", **kwargs)


def test_a_timeout_cancels_the_enrollment_and_waits_for_the_login_port(events):
    with pytest.raises(TimeoutError):
        enroll(on_login_url=lambda url: None, timeout=0.01)

    assert events == ["continue", "cancel", "wait"]


def test_a_failing_on_login_url_cancels_the_enrollment_and_waits_for_the_login_port(events):
    def on_login_url(url):
        raise KeyError(url)

    with pytest.raises(KeyError):
        enroll(on_login_url=on_login_url)

    assert events == ["cancel", "wait"]


def test_no_on_login_url_cancels_the_enrollment_and_waits_for_the_login_port(events):
    with pytest.raises(RuntimeError, match="on_login_url"):
        enroll()

    assert events == ["cancel", "wait"]


def test_an_enrollment_that_ended_has_nothing_to_cancel_or_wait_for(events):
    """The handle goes with any result of ``Ziti_enroll_continue`` but a timeout, and the listener went before it."""
    events.continue_result = INVALID_STATE

    with pytest.raises(RuntimeError):
        enroll(on_login_url=lambda url: None)

    assert events == ["continue"]


def accept_all(sock):
    """What a listener that is alive does: it takes every connection, so its queue never fills up (a full queue
    makes some systems refuse connections, which looks like a listener that is gone)."""
    sock.settimeout(0.1)
    while sock.fileno() != -1:
        try:
            sock.accept()[0].close()
        except TimeoutError:
            continue
        except OSError:
            return


@pytest.fixture
def listener():
    """A listening socket on the IPv6 loopback, on a port of its own: stands for the SDK's login listener."""
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        sock.bind(("::1", 0))
        sock.listen(1)
    except OSError:
        sock.close()
        pytest.skip("no IPv6 loopback")
    threading.Thread(target=accept_all, args=(sock,), daemon=True).start()
    yield sock
    sock.close()


@pytest.fixture
def login_port(monkeypatch, listener):
    port = listener.getsockname()[1]
    monkeypatch.setattr(zitilib, "_LOGIN_PORT", port)
    return port


def test_the_login_port_is_the_one_the_sdk_redirects_to():
    """``auth_cb_port`` in ziti-sdk-c's ``ext_oidc.c``: the redirect uri is always ``localhost:20314``."""
    assert zitilib._LOGIN_PORT == 20314


def test_the_wait_returns_when_the_listener_goes(login_port, listener):
    closed = []

    def close_later():
        time.sleep(0.3)
        listener.close()
        closed.append(time.monotonic())

    threading.Thread(target=close_later, daemon=True).start()

    zitilib._wait_for_login_port_to_free(timeout=10)
    returned = time.monotonic()

    assert closed, "returned while the listener was still there"
    assert returned - closed[0] < 2


def test_the_wait_gives_up_after_its_timeout_when_something_keeps_listening(login_port, listener):
    started = time.monotonic()

    zitilib._wait_for_login_port_to_free(timeout=0.5)  # no error: the next enrollment says what is wrong

    assert 0.4 <= time.monotonic() - started < 3


def test_there_is_nothing_to_wait_for_when_nothing_listens(monkeypatch):
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as free:
        try:
            free.bind(("::1", 0))
        except OSError:
            pytest.skip("no IPv6 loopback")
        monkeypatch.setattr(zitilib, "_LOGIN_PORT", free.getsockname()[1])
    started = time.monotonic()

    zitilib._wait_for_login_port_to_free(timeout=10)

    assert time.monotonic() - started < 1
