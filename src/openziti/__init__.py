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

from os import getenv

from . import _version, context, decor, zitilib, zitisock

_ziti_identities = filter(lambda p: p != '',
                          map(lambda s: s.strip(),
                              (getenv('ZITI_IDENTITIES') or "").split(';')))

enroll = zitilib.enroll
version = zitilib.version
shutdown = zitilib.shutdown
load = context.load_identity
socket = zitisock.ZitiSocket
ZitiContext = context.ZitiContext


for identity in _ziti_identities:
    if identity != '':
        load(identity)

monkeypatch = decor.MonkeyPatch
zitify = decor.zitify

from . import _version
__version__ = _version.get_versions()['version']
