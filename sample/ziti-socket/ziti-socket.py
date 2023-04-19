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
from socket import SOCK_STREAM,SHUT_WR


if __name__ == '__main__':
    # Use the provided intercept address or a default address from ZEDS
    intercept_address = 'httpbin.ziti'
    if len(sys.argv) > 1:
        intercept_address = sys.argv[1]
    # Use the provided port
    intercept_port = 80
    if len(sys.argv) > 2:
        intercept_port = sys.argv[2]
    print("Ziti SDK version = {0}".format(openziti.version()))
    sock = openziti.socket(type = SOCK_STREAM)
    sock.connect((intercept_address,
                  80))
    msg = """GET /json HTTP/1.1\r
Accept: */*\r
Accept-Encoding: gzip, deflate\r
Connection: keep-alive\r
Host: httpbin.org\r
User-Agent: HTTPie/3.1.0\r
\r
"""
    sock.send(bytes(msg, encoding = 'utf-8'))
    sock.shutdown(SHUT_WR)

    while 1:
        data = sock.recv(1024)
        if not data:
            break
        print(f'{data.decode("utf-8")}')

    openziti.shutdown()