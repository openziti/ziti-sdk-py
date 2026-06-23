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
import socket
import sys

from fastapi import FastAPI
from uvicorn import config, server

import openziti

app = FastAPI()

@app.get("/")
async def test_app():
    return {"status": "OK"}


class Server(server.Server):
    async def serve(self, sockets: list[socket.socket] | None = None) -> None:
        if not sockets:
            sockets = [self.config.bind_socket()]
        with self.capture_signals():
            await self._serve(sockets)


class BackendConfig(config.Config):
    def __init__(
        self,
        app,
        identity_file,
        service_name,
        ziti_load_timeout_ms=5000,
        backlog =2048,
    ):
        self.ztx, err = openziti.load(identity_file, timeout=ziti_load_timeout_ms)
        if err != 0:
            raise RuntimeError(f"Failed to load Ziti identity from {identity_file}: {err}")

        self.service_name = service_name
        self.ziti_load_timeout_ms = ziti_load_timeout_ms
        super().__init__(
            app,
            loop="asyncio",
            backlog=backlog,
        )

    def bind_socket(self) -> socket.socket:
        sock = self.ztx.bind(self.service_name)
        sock.listen(self.backlog)
        return sock


def main(id: str, svc: str):
    config = BackendConfig(
        app,
        identity_file=id,
        service_name=svc,
    )
    server_instance = Server(config)
    server_instance.startup()
    asyncio.run(server_instance.serve())


identity = sys.argv[1]
service = sys.argv[2]
if __name__ == "__main__":
    main(identity, service)