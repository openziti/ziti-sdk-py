#  Copyright NetFoundry Inc.
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

import sys
import openziti


def run(ziti_id, service):
    ztx = openziti.load(ziti_id)
    server = ztx.bind(service)
    server.listen()

    while True:
        conn, peer = server.accept()
        print(f'processing incoming client[{peer}]')
        with conn:
            count = 0
            while True:
                data = conn.recv(1024)
                if not data:
                    print(f'client finished after sending {count} bytes')
                    break
                count += len(data)
                conn.sendall(data)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])