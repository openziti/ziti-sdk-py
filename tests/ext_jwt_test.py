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

"""External JWT (OIDC) login through the SDK, with the in-process OIDC provider of ``oidc_idp.py``.

An ``ext-jwt-signer`` that trusts that provider (``idp_signer``) is the start of every test. Two kinds of
identity log in with it: one that has no cert (a bootstrap config: the controller's address and CA) and logs in
with the token alone, and one that has a cert and needs the token as secondary auth.

``ztx.login_external()`` gives out the url of the login page. The tests play the browser: they log in at the
provider and hand its redirect to the SDK's local listener.

The native calls that wait (``login_external``, ``wait_for_auth``) go through bounded helpers, so a call that
never returns fails its test instead of hanging the run: ``Ziti_login_external`` did not return before
ziti-sdk-c 1.22.1 (https://github.com/openziti/ziti-sdk-c/issues/1230).
"""

import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

import openziti
from openziti import ZitiContext
from .conftest import IDP_CLIENT_ID, IDP_REDIRECT_URI
from .util import ziti_edge

pytestmark = pytest.mark.require_ziti(">=2.0.0")

LOGIN_TIMEOUT = 10


class LoginHang(Exception):
    """``login_external`` did not return."""


class AuthWaitHang(Exception):
    """``wait_for_auth`` outlasted its own timeout."""


def _bounded(call, timeout, hang):
    """``call()`` that raises ``hang(...)`` instead of blocking the run for good.

    The native calls either have no timeout of their own or do not get the one they were given, and a thread that
    is stuck in one cannot be cancelled: it is left behind (it ends when the test's ``openziti.shutdown()``
    disables the context).
    """
    result = {}

    def run():
        try:
            result["value"] = call()
        except BaseException as e:  # handed to the test, this is not its thread
            result["error"] = e

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise hang(f"no return within {timeout}s")
    if "error" in result:
        raise result["error"]
    return result["value"]


def login_external(ztx, signer, timeout=LOGIN_TIMEOUT):
    """``ztx.login_external(signer)``: raises ``LoginHang`` when it does not return."""
    return _bounded(lambda: ztx.login_external(signer), timeout, LoginHang)


def wait_for_auth(ztx, seconds):
    """``ztx.wait_for_auth(seconds)``: fails the test when the wait outlasts its own timeout."""
    return _bounded(lambda: ztx.wait_for_auth(seconds), seconds + 10, AuthWaitHang)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


# loopback only: no proxies, and the interesting part of a login is the redirect itself
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)


def _get(url):
    try:
        with _opener.open(url, timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def deliver_redirect(url):
    """``GET`` the redirect of the idp, an url of ``localhost``, on whichever loopback address the SDK listens.

    The SDK's login listener is on the IPv6 loopback and a browser tries every address of ``localhost``. This
    does not resolve it: where ``localhost`` is ``127.0.0.1`` only (Ubuntu), it would never get there.
    """
    parts = urllib.parse.urlsplit(url)
    failure = None
    for host in ("[::1]", "127.0.0.1"):
        try:
            return _get(parts._replace(netloc=f"{host}:{parts.port}").geturl())
        except OSError as e:  # nothing listens there
            failure = e
    raise failure


def browse(idp, login_url, email, succeeds=True):
    """What the user does with the url ``login_external`` gave out: log in at the idp, follow its redirect.

    Returns the status of the SDK's page: the login succeeds with a 200, a controller that turns it down is a 401.
    """
    redirect = idp.login(login_url, email)
    status, body = deliver_redirect(redirect)
    if succeeds:
        assert status == 200, body
    return status


def echo(ztx, service):
    """Dial ``service`` right after ``wait_for_auth`` and get an echo: it returns once the services are loaded."""
    with ztx.connect(service, timeout=10) as sock:
        sock.send(b"hello")
        assert sock.recv(1024) == b"hello"


@pytest.fixture
def bootstrap_config(ziti_setup, tmp_path):
    """What an app has before it has an identity: the controller's address and CA, no cert or key."""
    cfg = json.loads(Path(ziti_setup["client"]).read_text())
    cfg["id"].pop("cert", None)
    cfg["id"].pop("key", None)
    path = tmp_path / "bootstrap.json"
    path.write_text(json.dumps(cfg))
    return str(path)


@pytest.fixture
def ext_identity(ziti_setup, idp_user):
    """The identity of ``idp_user`` (the external id is what the controller matches with the token) that may dial the service."""
    service = ziti_setup["service"]
    ziti_edge("create", "identity", idp_user, "--external-id", idp_user, "-a", "ext-client")
    ziti_edge("create", "service-policy", f"{service}-dial-ext", "Dial",
              "--identity-roles", f"@{idp_user}", "--service-roles", f"@{service}")
    return idp_user


@pytest.fixture
def secondary_ext_jwt(ziti_setup, idp_signer, idp_user):
    """Config of an identity that logs in with its cert and needs a token of ``idp_signer`` as secondary auth."""
    signers = ziti_edge("list", "ext-jwt-signers", f'name = "{idp_signer}"', "-j").stdout
    signer_id = json.loads(signers)["data"][0]["id"]  # the policy takes the id of the signer, not its name

    policy = f"{ziti_setup['service']}-cert-ext-jwt"
    ziti_edge("create", "auth-policy", policy,
              "--primary-cert-allowed", "--secondary-req-ext-jwt-signer", signer_id)
    # the controller matches the sub of the token with the external id of the identity
    ziti_edge("update", "identity", ziti_setup["client_name"],
              "--auth-policy", policy, "--external-id", idp_user)
    return ziti_setup["client"]


def test_bootstrap_config_requires_external_login(bootstrap_config, idp_signer):
    ztx, err = openziti.load(bootstrap_config)
    assert err == ZitiContext.EXTERNAL_LOGIN_REQUIRED, openziti.strerror(err)


def test_external_signer_is_listed(bootstrap_config, idp_signer):
    ztx, _ = openziti.load(bootstrap_config)
    assert idp_signer in ztx.get_external_signers()


def test_wait_for_auth_times_out_while_login_is_pending(bootstrap_config, idp_signer):
    ztx, _ = openziti.load(bootstrap_config)
    assert wait_for_auth(ztx, 1) != 0


def test_login_external_with_unknown_signer_fails(bootstrap_config, idp_signer):
    ztx, _ = openziti.load(bootstrap_config)
    with pytest.raises(Exception) as excinfo:
        login_external(ztx, "no-such-signer")
    assert not isinstance(excinfo.value, LoginHang)


def test_secondary_ext_jwt_requires_login(secondary_ext_jwt, idp_signer):
    ztx, err = openziti.load(secondary_ext_jwt)
    assert err == ZitiContext.PARTIALLY_AUTHENTICATED, openziti.strerror(err)
    assert idp_signer in ztx.get_external_signers()


def test_login_external_returns_the_idp_login_url(bootstrap_config, idp, idp_signer):
    ztx, _ = openziti.load(bootstrap_config)
    url = urllib.parse.urlsplit(login_external(ztx, idp_signer))
    query = urllib.parse.parse_qs(url.query)

    assert f"{url.scheme}://{url.netloc}{url.path}" == f"{idp.issuer}/authorize"
    assert query["client_id"] == [IDP_CLIENT_ID]
    assert query["response_type"] == ["code"]
    assert query["redirect_uri"] == [IDP_REDIRECT_URI]
    assert query["code_challenge_method"] == ["S256"]  # PKCE: the idp has no secret to check
    assert query["code_challenge"]


def test_external_login_authenticates_and_dials(echo_server_process, ziti_setup, ext_identity, bootstrap_config,
                                                idp, idp_signer, idp_user):
    ztx, err = openziti.load(bootstrap_config)
    assert err == ZitiContext.EXTERNAL_LOGIN_REQUIRED, openziti.strerror(err)

    browse(idp, login_external(ztx, idp_signer), idp_user)

    rc = wait_for_auth(ztx, 30)
    assert rc == 0, openziti.strerror(rc)
    echo(ztx, ziti_setup["service"])


def test_external_login_of_unknown_identity_is_rejected(bootstrap_config, idp, idp_signer, idp_user):
    """The idp knows the user, the network has no identity for it: the controller turns the token down."""
    ztx, _ = openziti.load(bootstrap_config)

    status = browse(idp, login_external(ztx, idp_signer), idp_user, succeeds=False)

    assert status != 200  # the SDK's page says the login failed
    assert wait_for_auth(ztx, 20) != 0


def test_secondary_ext_jwt_login_and_dial(echo_server_process, ziti_setup, secondary_ext_jwt, idp, idp_signer,
                                          idp_user):
    ztx, err = openziti.load(secondary_ext_jwt)
    assert err == ZitiContext.PARTIALLY_AUTHENTICATED, openziti.strerror(err)

    browse(idp, login_external(ztx, idp_signer), idp_user)

    rc = wait_for_auth(ztx, 30)
    assert rc == 0, openziti.strerror(rc)
    echo(ztx, ziti_setup["service"])
