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

import json
import logging
import os
import ssl
import subprocess
import urllib.request

import pytest

import openziti

logger = logging.getLogger(__name__)
ziti_executable = os.environ.get("ZITI_CLI", "ziti")

# the ``quickstart`` fixture lets ziti pick its default port
CTRL_URL = "https://127.0.0.1:1280"

def ziti_edge(*args, check=True):
    """Run a ``ziti edge`` subcommand."""
    result = subprocess.run(
        [ziti_executable, "edge"] + list(args),
        capture_output=True, text=True,
    )
    logger.info("ziti edge %s -> rc=%d", " ".join(args), result.returncode)
    if result.stdout:
        logger.info(result.stdout.rstrip())
    if result.stderr:
        logger.info(result.stderr.rstrip())
    if check and result.returncode != 0:
        pytest.fail(f"ziti edge {' '.join(args)} failed: {result.stderr}")
    return result


def create_service(name: str, dialer: str, binder: str, intercept: str | dict | None = None ):
    if isinstance(intercept, dict):
        intercept = json.dumps(intercept)

    ziti_edge("create", "service", name)
    if intercept is not None:
        ziti_edge("create", "config", f"{name}-intercept", "intercept.v1", intercept)
        ziti_edge("update", "service", name, "-c", f"{name}-intercept")

    ziti_edge("create", "service-policy", f"{name}-dial", "Dial",
              "--identity-roles", f"@{dialer}",
              "--service-roles", f"@{name}")
    ziti_edge("create", "service-policy", f"{name}-bind", "Bind",
              "--identity-roles", f"@{binder}",
              "--service-roles", f"@{name}")


def create_identity(name: str, jwt: str) -> str:
    ziti_edge("create", "identity", name, "-o", jwt)
    return jwt


def enroll_identity(jwt: str) -> str:
    cfg = openziti.enroll(jwt)
    return cfg


def identities_of(external_id: str) -> list[dict]:
    """The identities of the network that have this external id."""
    out = ziti_edge("list", "identities", f'externalId = "{external_id}"', "-j").stdout
    return json.loads(out)["data"]


def fetch_network_jwt() -> str:
    """The controller's network JWT: what an app that does not trust the controller yet verifies it with."""
    # the controller's certificate is not signed by anything this python trusts; it is our own, on loopback
    tls = ssl.create_default_context()
    tls.check_hostname = False
    tls.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=tls))
    with opener.open(f"{CTRL_URL}/network-jwts", timeout=10) as resp:
        return json.load(resp)["data"][0]["token"]

