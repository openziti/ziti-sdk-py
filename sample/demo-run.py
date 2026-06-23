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
import signal
import subprocess
import threading

logger = logging.getLogger(__name__)
ziti_executable = os.environ.get("ZITI_CLI", "ziti")

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
        raise RuntimeError(f"ziti edge {' '.join(args)} failed: {result.stderr}")
    return result

def quickstart():
    ready = threading.Event()
    proc = subprocess.Popen(
        [ziti_executable, "edge", "quickstart",
         "--ctrl-address=127.0.0.1",
         "--router-address=127.0.0.1",
         ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    def _reader():
        with open("qs.log", mode="wt+") as qs_log:
            for line in proc.stdout:
                print(line, file=qs_log)
                if "controller and router started" in line:
                    ready.set()

    t = threading.Thread(target=_reader, daemon=True)
    t.start()

    if not ready.wait(timeout=300):
        proc.kill()
        raise TimeoutError("quickstart did not become ready within 300s")

    return proc

def create_demo_model():
    import openziti
    import json
    intercept = {
        "protocols": ["tcp", "udp"],
        "portRanges": [{"low": 80, "high": 80}],
        "addresses": ["demo.service.ziti"],
    }
    ziti_edge("create", "identity", "demo-server", "-o", "demo-server.jwt")
    ziti_edge("create", "identity", "demo-client", "-o", "demo-client.jwt")
    ziti_edge("create", "config", "demo-intercept", "intercept.v1", json.dumps(intercept))
    ziti_edge("create", "service", "demo-service", "-c", "demo-intercept")
    ziti_edge("create", "service-policy", "demo-service-dial", "Dial",
              "--identity-roles", "@demo-client",
              "--service-roles", "@demo-service")
    ziti_edge("create", "service-policy", "demo-service-bind", "Bind",
              "--identity-roles", "@demo-server",
              "--service-roles", "@demo-service")

    with open("demo-client.json", "w") as f:
        print(openziti.enroll("demo-client.jwt"), file=f)
        os.unlink("demo-client.jwt")

    with open("demo-server.json", "w") as f:
        print(openziti.enroll("demo-server.jwt"), file=f)
        os.unlink("demo-server.jwt")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    proc = quickstart()
    print("quickstart is running with PID:", proc.pid)
    create_demo_model()
    print("=" * 50)
    print("you are ready to run samples:")
    print("service name: demo-service")
    print("client identity: demo-client.json")
    print("server identity: demo-server.json")
    print("intercept name: demo.service.ziti")
    print("=" * 50)
    print("Ctrl-C to stop...")
    print()

    def on_signal(sig, frame):
        print("stopping demo network..")
        proc.kill()

    signal.signal(signal.SIGINT, on_signal)
    proc.wait()
    print("demo network stopped")
