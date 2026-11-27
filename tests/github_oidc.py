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

"""The GitHub Actions OIDC token of the job that runs the tests, and the signer that trusts it.

This is how a workflow gets onto a Ziti network without an identity in its secrets: it asks GitHub for an OIDC
token, and an ext-jwt-signer that trusts GitHub (``--enroll-to-token``) creates the identity of the repository on
the first login. The tokens exist only inside a job that has ``id-token: write`` (``wheels.yml`` has it), so
everywhere else (a laptop, a pull request from a fork) the tests that need one are skipped.
"""

import base64
import json
import os
import urllib.parse
import urllib.request

import pytest

from .util import ziti_edge

GH_ISSUER = "https://token.actions.githubusercontent.com"
GH_AUDIENCE = "ziti-sdk-py-ci"
GH_SIGNER = "github-actions-signer"

in_job = bool(os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL"))
requires_job = pytest.mark.skipif(not in_job, reason="not a GitHub Actions job that has `id-token: write`")


def _get_json(url, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=30) as resp:
        return json.load(resp)


def token():
    """A token of this job for ``GH_AUDIENCE``. They do not live long, so ask right before one is used."""
    url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"] + "&audience=" + urllib.parse.quote(GH_AUDIENCE)
    bearer = os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
    return _get_json(url, {"Authorization": f"bearer {bearer}"})["value"]


def claims(jwt):
    payload = jwt.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


def create_signer():
    """Create the ext-jwt-signer that trusts GitHub, names an identity after the repository and enrolls it to a token.

    GitHub has no login to start and the SDK selects no signer: no IdP url and no client id.
    """
    jwks = _get_json(f"{GH_ISSUER}/.well-known/openid-configuration")["jwks_uri"]
    ziti_edge("create", "ext-jwt-signer", GH_SIGNER, GH_ISSUER,
              "--jwks-endpoint", jwks,
              "--audience", GH_AUDIENCE,
              "--claims-property", "repository",
              "--enroll-to-token",
              "--enroll-name-claims-selector", "/repository")
    return GH_SIGNER
