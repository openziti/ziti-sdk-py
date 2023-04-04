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
from http.server import BaseHTTPRequestHandler, HTTPServer

import openziti

hostName = "127.0.0.1"
serverPort = 18080

cfg = dict(
    ztx=openziti.load('/Users/geoffberl/python.flask.json'),
    service="python.flask"
)
openziti.monkeypatch(bindings={(hostName, serverPort): cfg})


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        msg = """{"msg": "Help! I was zitified!"}"""
        self.wfile.write(bytes(msg, "utf-8"))


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever(poll_interval=600)
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")