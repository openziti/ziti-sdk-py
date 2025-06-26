#  Copyright (c) 2022.  NetFoundry, Inc.
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
import os
import time
import unittest
import requests
from requests.exceptions import ConnectionError
from tests.run_ziti import *

def get_httpbin(url):
    return requests.get(url)

class TestZitiModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("💥 setting up ziti", flush=True)
        cls.ziti_path = get_ziti(add_to_path=False)
        cls.proc = start_ziti_quickstart(cls.ziti_path)
        wait_for_controller()
        print("✅ ziti is up", flush=True)
        login(cls.ziti_path)
        create_and_enroll_identities(cls.ziti_path)
        os.environ["ZITI_IDENTITIES"] = os.path.join(os.getcwd(), "pytest.json")
        create_service(cls.ziti_path)
        cls.flask_proc = start_flask_app()
        print("---- FLASK STARTED ----")
        global openziti
        import openziti
        print(f"✅ imported openziti: {openziti.__version__}", flush=True)
        wait_for_terminator(ziti=cls.ziti_path)

    @classmethod
    def tearDownClass(cls):
        print("🛑 tearing down", flush=True)
        start = time.time()

        def safe_terminate(proc, name):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=10)
                except Exception:
                    print(f"⚠️ {name} did not terminate gracefully, killing", flush=True)
                    proc.kill()
            else:
                print(f"ℹ️ {name} already terminated", flush=True)

        safe_terminate(cls.flask_proc, "flask_proc")
        safe_terminate(cls.proc, "ziti_quickstart")

        print(f"✅ terminated in {time.time() - start:.2f}s", flush=True)

    def test_monkeypatch(self):
        print("test_monkeypatch: " + os.environ["ZITI_IDENTITIES"])
        with self.assertRaises(ConnectionError):
            get_httpbin('http://httpbin.ziti/json')

        with openziti.monkeypatch():
            from json import dumps
            r = get_httpbin('http://httpbin.ziti/json')
            self.assertEqual(r.status_code, 200, f"got {r.status_code}, body: {r.text}")
            body = r.json()
            print(dumps(body, indent=2))
            self.assertRegex(r.headers['Server'], 'waitress')

        with self.assertRaises(ConnectionError):
            get_httpbin('http://httpbin.ziti/json')

    def test_resolve(self):
        print("test_resolve: " + os.environ["ZITI_IDENTITIES"])
        with openziti.monkeypatch():
            import socket
            addrlist = socket.getaddrinfo(host='httpbin.ziti', port=80, type=socket.SOCK_STREAM)
            assert len(addrlist) == 1
            af, socktype, proto, name, addr = addrlist[0]
            assert af == socket.AF_INET
            assert socktype == socket.SOCK_STREAM
            assert proto == socket.IPPROTO_TCP
            assert isinstance(addr, tuple)
            assert isinstance(addr[0], str)
            assert isinstance(addr[1], int)
            assert addr[1] == 80
            assert addr[0].startswith('100.64.0.')
            print(f"resolved addr to {addr[0]}")

    def test_monkeypatch_bypass(self):
        print("test_monkeypatch_bypass: " + os.environ["ZITI_IDENTITIES"])
        with openziti.monkeypatch():
            from json import dumps
            r = get_httpbin('https://httpbin.org/json')
            self.assertEqual(r.status_code, 200, f"got {r.status_code}, body: {r.text}")
            body = r.json()
            print(dumps(body, indent=2))
            self.assertRegex(r.headers['Content-Type'], 'application/json')

