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
import unittest
import openziti
import requests
from requests.exceptions import ConnectionError

def get_httpbin(url):
    return requests.get(url)


@unittest.skipIf(os.getenv('ZITI_IDENTITIES') is None, 'no test identity')
class TestZitiModule(unittest.TestCase):

    def test_monkeypatch(self):
        with self.assertRaises(ConnectionError):
            get_httpbin('http://httpbin.ziti/json')

        with openziti.monkeypatch():
            from json import dumps
            r = get_httpbin('http://httpbin.ziti/anything')
            assert r.status_code == 200
            body = r.json()
            print(dumps(body, indent=2))
            self.assertRegex(body['headers']['User-Agent'], r'python-requests/.*')

        with self.assertRaises(ConnectionError):
            get_httpbin('http://httpbin.ziti/json')

