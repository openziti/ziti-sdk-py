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

"""Enrollment through an external identity provider (``enroll_with_idp``) and login with the token an app holds.

The controller trusts an ext-jwt-signer and, for a token of that signer, creates the identity (``enroll to token``:
it has no cert, the token is its login; ``enroll to cert``: the controller signs a CSR for the token). The app has
only the network JWT of the controller, which is its trust anchor.

The in-process OIDC provider of ``oidc_idp.py`` stands for the IdP. The tests that hand the app a token it already
holds also run with the GitHub Actions token of the job (``github_oidc.py``) wherever there is one: that is how a
workflow gets onto a network without an identity in its secrets.
"""

import json
from dataclasses import dataclass
from typing import Callable

import pytest

import openziti
from openziti import EnrollMode, ZitiContext
from . import github_oidc
from .ext_jwt_test import browse, wait_for_auth
from .util import identities_of, ziti_edge

pytestmark = pytest.mark.require_ziti(">=2.0.0")


@dataclass
class TokenSource:
    """Where an app that holds a token gets it, and the identity the signer makes of it."""
    subject: str                # the external id of the identity: it is what the controller matches the token with
    mint: Callable[[], str]     # a fresh token: they do not live long


@pytest.fixture
def github_source(github_signer):
    """The token of this job; the identity of its repository goes when the test is done, so the next one enrolls it again."""
    repository = github_oidc.claims(github_oidc.token())["repository"]
    yield TokenSource(repository, github_oidc.token)
    ziti_edge("delete", "identity", "where", f'externalId = "{repository}"', check=False)


@pytest.fixture(params=["idp", pytest.param("github", marks=github_oidc.requires_job)])
def token_source(request):
    """A signer that enrolls to a token, with the token of the in-process idp or of this GitHub Actions job."""
    if request.param == "github":
        return request.getfixturevalue("github_source")
    idp, user = request.getfixturevalue("idp"), request.getfixturevalue("idp_user")
    request.getfixturevalue("enroll_mode")("token")
    return TokenSource(user, lambda: idp.password_grant(user)["access_token"])


def write_identity(identity_json, tmp_path, name="identity.json"):
    path = tmp_path / name
    path.write_text(identity_json)
    return str(path)


def login_url_opener(idp, email):
    """An ``on_login_url`` that plays the user: it logs in at the idp and follows its redirect to the SDK."""
    urls = []

    def on_login_url(url):
        urls.append(url)
        browse(idp, url, email)

    on_login_url.urls = urls
    return on_login_url


def test_enroll_to_token_then_log_in_with_the_token(network_jwt, token_source, tmp_path):
    assert not identities_of(token_source.subject), "nothing could have enrolled this subject yet"

    identity = openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, token_source.mint())

    # enrolled to a token: the controller made the identity, and the config has no cert or key
    assert len(identities_of(token_source.subject)) == 1
    id_cfg = json.loads(identity)["id"]
    assert id_cfg.get("ca")
    assert not id_cfg.get("cert") and not id_cfg.get("key")

    ztx, err = openziti.load(write_identity(identity, tmp_path))
    assert err == ZitiContext.EXTERNAL_LOGIN_REQUIRED, openziti.strerror(err)

    # a token that cannot be used is turned down at once, and the context keeps waiting for a login
    with pytest.raises(RuntimeError):
        ztx.login_with_token("not a jwt")

    ztx.login_with_token(token_source.mint())
    rc = wait_for_auth(ztx, 30)
    assert rc == 0, openziti.strerror(rc)


def test_enroll_to_cert_gives_an_identity_that_logs_in_on_its_own(network_jwt, idp, idp_user, enroll_mode, tmp_path):
    enroll_mode("cert")

    identity = openziti.enroll_with_idp(network_jwt, EnrollMode.CERT, idp.password_grant(idp_user)["access_token"])

    assert len(identities_of(idp_user)) == 1
    id_cfg = json.loads(identity)["id"]
    assert id_cfg.get("cert") and id_cfg.get("key")

    # the cert is the login: no external login is asked for
    ztx, err = openziti.load(write_identity(identity, tmp_path))
    assert err == 0, openziti.strerror(err)


def test_enroll_none_gives_the_bootstrap_config(network_jwt):
    """No idp in mode none: the controller's address and CA, nothing that identifies anyone."""
    cfg = json.loads(openziti.enroll_with_idp(network_jwt, EnrollMode.NONE))

    assert cfg["ztAPI"]
    assert cfg["id"].get("ca")
    assert not cfg["id"].get("cert") and not cfg["id"].get("key")


def test_log_in_with_a_token_to_a_precreated_identity(network_jwt, idp, idp_signer, idp_user, tmp_path):
    """``enroll none``: the identity exists already, and its external id is the ``sub`` of the token."""
    ziti_edge("create", "identity", idp_user, "--external-id", idp_user)

    bootstrap = openziti.enroll_with_idp(network_jwt, EnrollMode.NONE)
    ztx, err = openziti.load(write_identity(bootstrap, tmp_path))
    assert err == ZitiContext.EXTERNAL_LOGIN_REQUIRED, openziti.strerror(err)

    ztx.login_with_token(idp.password_grant(idp_user)["access_token"])
    rc = wait_for_auth(ztx, 30)
    assert rc == 0, openziti.strerror(rc)


def test_enroll_with_a_signer_name_that_the_controller_does_not_have(network_jwt, idp_signer, enroll_mode):
    """An idp that is not a token is a signer name; there is nothing to log in with, so it is turned down at once."""
    enroll_mode("token")

    with pytest.raises(RuntimeError):
        openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, "no-such-signer")


def test_enroll_with_a_signer_logs_in_in_the_browser(network_jwt, idp, idp_signer, idp_user, enroll_mode):
    """A login with a signer is interactive: ``on_login_url`` gets the url the user has to open."""
    enroll_mode("token")
    browser = login_url_opener(idp, idp_user)

    identity = openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, idp_signer, on_login_url=browser, timeout=30)

    assert [u.split("?")[0] for u in browser.urls] == [f"{idp.issuer}/authorize"]
    assert len(identities_of(idp_user)) == 1
    id_cfg = json.loads(identity)["id"]  # enrolled to a token: no cert, the token is the login
    assert id_cfg.get("ca") and not id_cfg.get("cert")


def test_enroll_without_a_signer_name_logs_in_with_the_first_signer(network_jwt, idp, idp_signer, idp_user, enroll_mode):
    """No idp at all: the first signer that offers the enrollment mode is the one."""
    enroll_mode("token")
    browser = login_url_opener(idp, idp_user)

    openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, on_login_url=browser, timeout=30)

    assert len(browser.urls) == 1
    assert len(identities_of(idp_user)) == 1


def test_enroll_that_needs_a_login_without_on_login_url_is_abandoned(network_jwt, idp, idp_signer, idp_user,
                                                                      enroll_mode):
    """There is nobody to tell the url to: it fails, and the SDK is free for the next enrollment (one is pending at a time)."""
    enroll_mode("token")

    with pytest.raises(RuntimeError, match="on_login_url"):
        openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, idp_signer)

    openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, idp_signer,
                             on_login_url=login_url_opener(idp, idp_user), timeout=30)
    assert len(identities_of(idp_user)) == 1


def test_enroll_that_is_not_logged_in_times_out_and_is_abandoned(network_jwt, idp, idp_signer, idp_user, enroll_mode):
    enroll_mode("token")
    urls = []

    with pytest.raises(TimeoutError):
        openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, idp_signer, on_login_url=urls.append, timeout=0.5)
    assert len(urls) == 1
    assert not identities_of(idp_user)

    # the pending enrollment is gone, not left to block the next one
    openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, idp_signer,
                             on_login_url=login_url_opener(idp, idp_user), timeout=30)
    assert len(identities_of(idp_user)) == 1


def test_enroll_whose_on_login_url_fails_is_abandoned(network_jwt, idp, idp_signer, idp_user, enroll_mode):
    enroll_mode("token")

    class Boom(Exception):
        pass

    def on_login_url(url):
        raise Boom(url)

    with pytest.raises(Boom):
        openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, idp_signer, on_login_url=on_login_url, timeout=30)

    openziti.enroll_with_idp(network_jwt, EnrollMode.TOKEN, idp_signer,
                             on_login_url=login_url_opener(idp, idp_user), timeout=30)
    assert len(identities_of(idp_user)) == 1
