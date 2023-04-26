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

from flask import Flask
import openziti
import sys

app = Flask(__name__)
bind_opts = {}  # populated in main


@openziti.zitify(bindings={
    ':18080': bind_opts,
})
def runApp():
    from waitress import serve
    serve(app,port=18080)


@app.route('/')
def hello_world():  # put application's code here
    return 'Have some Ziti!'


if __name__ == '__main__':
    bind_opts['ztx'] = sys.argv[1]
    bind_opts['service'] = sys.argv[2]
    runApp()
