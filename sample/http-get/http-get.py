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
import urllib3
import openziti

# to run this sample
# set ZITI_IDENTITIES environment variable to location of your Ziti identity file
#
# python http-get.py <url>
# url should be the intercept address of a ziti service
if __name__ == '__main__':
    openziti.monkeypatch()
    http = urllib3.PoolManager()
    r = http.request('GET', sys.argv[1])
    print("{0} {1}".format(r.status, r.reason))
    print(r.data.decode('utf-8'))

