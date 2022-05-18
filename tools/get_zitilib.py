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

import sys
import sysconfig
from os.path import dirname

ZITI_SDK_BASE = 'https://github.com/openziti/ziti-sdk-c/releases/download'


def download_sdk(plat, version):
    from urllib.request import Request
    from urllib.request import urlopen
    from urllib.error import HTTPError

    osname, arch = plat.split('-')
    filename = f'{ZITI_SDK_BASE}/{version}/ziti-sdk-{version}-{osname}-{arch}.zip'
    headers = dict()
    req = Request(url=filename, headers=headers)
    try:
        response = urlopen(req)
    except HTTPError:
        print(f'Could not download "{filename}"', file=sys.stderr)
        raise
    length = response.getheader('content-length')
    if response.status != 200:
        print(f'Could not download "{filename}"', file=sys.stderr)
        return None

    print(f"Downloading {length} from {filename}", file=sys.stderr)
    return response.read()


def extract(data, libname):
    from io import BytesIO
    import zipfile
    zip = zipfile.ZipFile(BytesIO(data))
    return zip.extract(member=f'lib/{libname}',path=f'src/openziti/')


def get_sdk_version():
    from configparser import ConfigParser
    cfgfile = f'{dirname(__file__)}/../setup.cfg'
    parser = ConfigParser()
    parser.read(cfgfile)
    return dict(parser.items('openziti'))['ziti_sdk_version']


if __name__ == '__main__':
    sdk_version = get_sdk_version()
    platform = sysconfig.get_platform()
    osname, arch = platform.split('-')
    osname = osname.capitalize()
    libname = None
    if osname == 'Linux':
        libname = 'libziti.so'
    elif osname == 'Darwin':
        libname = 'libziti.dylib'
    elif osname == 'win64':
        libname = 'ziti.dll'

    d = download_sdk(platform, version=sdk_version)
    libfile = extract(d, libname)
