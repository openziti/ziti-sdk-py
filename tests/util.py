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
import pytest
import subprocess

from conftest import ziti_executable

logger = logging.getLogger(__name__)

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
    if intercept is dict:
        intercept = json.dumps(intercept)

    ziti_edge("create", "service", name)
    if intercept is not None:
        ziti_edge("create", "config", f"{name}-intercept", "intercept.v1", intercept)
        ziti_edge("update", "service", name, "-c", f"{name}-intercept")

    ziti_edge("create", "service-policy", "Dial", f"{name}-dial",
              "--identity-roles", dialer,
              "--service-roles", name)
    ziti_edge("create", "service-policy", "Bind", f"{name}-bind",
              "--identity-roles", binder,
              "--service-roles", name)


def create_identity(name: str, jwt: str):
    ziti_edge("create", "identity", name, "-o", jwt)