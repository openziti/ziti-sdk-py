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
import asyncio
import logging
import os
import subprocess
import threading
from multiprocessing import Process

import flask
import waitress
from semver import Version

import pytest

logger = logging.getLogger(__name__)
ziti_executable = os.environ.get("ZITI_CLI", "ziti")

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
    logger.warning("require_ziti marker: %s", marker)
    if marker:
        req_ver = marker.args[0]
        logger.warning("require_ziti: required=%s, actual=%s", req_ver, ziti_version)
        if not ziti_version.match(req_ver):
            pytest.skip(f"Skipped because ziti version is {ziti_version} does not match {req_ver}")


@pytest.fixture(scope="session")
def quickstart():
    pass


@pytest.fixture
def echo_flask(request):
    loop = asyncio.new_event_loop()

    async def echo(input: asyncio.StreamReader, output: asyncio.StreamWriter):
        client_address = output.get_extra_info('peername')
        print(f"[+] New connection established from {client_address}")
        bts = await input.read()
        if not bts:
            return
        output.write(bts)

    async def run():
        await asyncio.start_server(echo, port=8080)
    task = loop.create_task(run(), eager_start=True)
    thread = threading.Thread(target=loop.run_forever)
    thread.start()
    yield
    task.cancel()
    thread.join()


import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio


# 1. Define a dummy echo handler for our server
async def echo_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    while True:
        data = await reader.read(100)
        if not data:
            break
        writer.write(data)
        await writer.drain()
        writer.write(data)
        await writer.drain()


# 2. Build the async server fixture
@pytest_asyncio.fixture
async def echo_server() -> AsyncGenerator[str, None]:
    host = "127.0.0.1"

    # Start the server using the provided background event loop
    server = await asyncio.start_server(echo_handler, host, port=8080)
    logger.info(f"server {server.sockets[0].getsockname()}")
    # Yield the address to the test functions
    yield server.sockets[0].getsockname()

    # Teardown: Stop the server cleanly after the test finishes
    server.close()
    await server.wait_closed()


# 3. Write your async test case
@pytest.mark.asyncio
async def test_echo_server(tcp_server: str):
    # Split out host and port from the fixture string
    _, host_port = tcp_server.split("//")
    host, port = host_port.split(":")

    # Act: Connect to the server spun up by the fixture
    reader, writer = await asyncio.open_connection(host, int(port))
    writer.write(b"Hello Server")
    await writer.drain()

    response = await reader.read(100)
    assert response == b"Hello Server"

    writer.close()
    await writer.wait_closed()

