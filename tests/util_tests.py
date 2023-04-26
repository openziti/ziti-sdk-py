#  Copyright (c)  NetFoundry Inc.
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
import unittest


class TestZitiModule(unittest.TestCase):
    def test_normalize_addresses(self):
        from openziti.zitisock import process_bindings
        orig = {
            ('localhost', 8080): "address1",
            ('localhost', '8081'): "address2",
            ('', 8082): "address3",
            'localhost:8083': "address4",
            ':8084': "address5",
            8085: "address6",
        }

        expected = {
            ('localhost', 8080): "address1",
            ('localhost', 8081): "address2",
            ('0.0.0.0', 8082): "address3",
            ('localhost', 8083): "address4",
            ('0.0.0.0', 8084): "address5",
            ('0.0.0.0', 8085): "address6",
        }

        norm = process_bindings(orig)
        self.assertEquals(norm, expected)
