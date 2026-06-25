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
import logging
import os
import subprocess
import sys
import threading
import time

import pytest
from semver import Version

import openziti
from .util import create_identity, create_service, enroll_identity, ziti_executable

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def ziti_version():
    result = subprocess.run([ziti_executable, "version"], capture_output=True, text=True, check=True)
    ver_str = result.stdout.strip().lstrip("v")
    ver_str = "+build.".join(ver_str.split("-")[:2])
    logger.info("Ziti CLI version string: '%s'", ver_str)
    return Version.parse(ver_str)

@pytest.fixture(autouse=True)
def require_ziti(ziti_version, request):
    marker = request.node.get_closest_marker("require_ziti")
    logger.info("require_ziti marker: %s", marker)
    if marker:
        req_ver = marker.args[0]
        logger.info("require_ziti: required=%s, actual=%s", req_ver, ziti_version)
        if not ziti_version.match(req_ver):
            pytest.skip(f"Skipped because ziti version is {ziti_version} does not match {req_ver}")

@pytest.fixture(autouse=True)
def init():
    """cleans up zitilib between tests"""
    openziti.zitilib.init()
    yield
    openziti.shutdown()


@pytest.fixture(scope="session")
def quickstart(tmpdir_factory):
    qs_home = tmpdir_factory.mktemp("qs")
    os.makedirs(qs_home, exist_ok=True)

    ready = threading.Event()
    proc = subprocess.Popen(
        [ziti_executable, "edge", "quickstart",
         "--home", qs_home,
         "--ctrl-address=127.0.0.1",
         "--router-address=127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    with open(f"{qs_home}/qs.log", "wt") as qs_log:
        def _reader():
            for line in proc.stdout:
                qs_log.write(line)
                if "controller and router started" in line:
                    ready.set()

        t = threading.Thread(target=_reader, daemon=True)
        t.start()

        if not ready.wait(timeout=90):
            proc.kill()
            pytest.fail("quickstart did not become ready within 90s")

        yield proc

        proc.terminate()
        try:
            code = proc.wait(timeout=10)
            print(f"quickstart process exited with code {code}", file=qs_log)
        except subprocess.TimeoutExpired:
            print(f"killing quickstart process", file=qs_log)
            proc.kill()
            proc.wait()


@pytest.fixture
def ziti_setup(quickstart, request, tmp_path):
    """simple test setup: client, server, service with intercept"""
    name = request.node.name
    client_name = f"client_{name}"
    server_name = f"server_{name}"
    client_jwt = create_identity(client_name, f"{tmp_path}/client.jwt")
    server_jwt = create_identity(server_name, f"{tmp_path}/server.jwt")

    hostname = f"{name}.ziti.test"
    intercept = {
        "protocols": ["tcp", "udp"],
        "portRanges": [{"low": 80, "high": 80}],
        "addresses": [hostname],
    }

    create_service(name, dialer=client_name, binder=server_name, intercept=intercept)

    client_json = f"{tmp_path}/client.json"
    with open(client_json, "wt") as f:
        print(enroll_identity(client_jwt), file=f)
    server_json = f"{tmp_path}/server.json"
    with open(server_json, "wt") as f:
        print(enroll_identity(server_jwt), file=f)

    return dict(
        client = client_json,
        server = server_json,
        service = name,
        intercept = intercept,
    )


@pytest.fixture
def echo_server_process(ziti_setup, tmp_path):
    identity = str(ziti_setup["server"])
    service_name = str(ziti_setup["service"])
    env = os.environ.copy()
    env["ZITI_LOG"] = "5"
    with open(f'{tmp_path}/echo.log', 'wt') as log:
        p = subprocess.Popen(
            [sys.executable,
             "sample/ziti-echo-server/ziti-echo-server.py",
             identity, service_name],
            stdout=log, stderr=subprocess.STDOUT, env=env,
            text=True)
        logger.info("started echo server subprocess with PID %d", p.pid)
        time.sleep(3)
        yield
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            logger.warning("echo server did not terminate in time, killing")
            p.kill()


@pytest.fixture
def uvicorn_process(ziti_setup, tmp_path):
    identity = str(ziti_setup["server"])
    service_name = str(ziti_setup["service"])
    env = os.environ.copy()
    env["ZITI_LOG"] = "5"
    with open(f'{tmp_path}/uvicorn.log', 'wt') as log:
        p = subprocess.Popen(
            [sys.executable,
             "sample/ziti-uvicorn/ziti-uvicorn.py",
             identity, service_name],
            stdout=log, stderr=subprocess.STDOUT, env=env,
            text=True)
        logger.info("started uvicorn server subprocess with PID %d", p.pid)
        time.sleep(3)
        yield
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            logger.warning("uvicorn server did not terminate in time, killing")
            p.kill()
