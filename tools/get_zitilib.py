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
import zipfile
from configparser import ConfigParser
from io import BytesIO
from os.path import dirname
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ZITI_SDK_BASE = 'https://github.com/openziti/ziti-sdk-c/releases/download'


def download_sdk(version):
    filename = f'{ZITI_SDK_BASE}/{version}/ziti-sdk-{version}-{osname}-{arch}.zip'
    headers = {}
    req = Request(url=filename, headers=headers)
    try:
        with urlopen(req) as response:
            length = response.getheader('content-length')
            if response.status != 200:
                print(f'Could not download "{filename}"', file=sys.stderr)
                return None

            print(f"Downloading {length} from {filename}", file=sys.stderr)
            return response.read()
    except HTTPError:
        print(f'Could not download "{filename}"', file=sys.stderr)
        raise


def extract(data, libname):
    with zipfile.ZipFile(BytesIO(data)) as zipf:
        return zipf.extract(member=f'lib/{libname}', path='src/openziti/')


def get_sdk_version():
    cfgfile = f'{dirname(__file__)}/../setup.cfg'
    parser = ConfigParser()
    parser.read(cfgfile)
    return dict(parser.items('openziti'))['ziti_sdk_version']


if __name__ == '__main__':
    import platform
    sdk_version = get_sdk_version()
    osname = platform.system()
    arch = platform.machine()
    print(f'platform={osname}-{arch}')

    osname = osname.capitalize()
    if osname == 'Linux':
        LIBNAME = 'libziti.so'
    elif osname == 'Darwin':
        LIBNAME = 'libziti.dylib'
    elif osname == 'Windows':
        LIBNAME = 'ziti.dll'
    else:
        raise RuntimeError("Unsupported platform/arch")

    d = download_sdk(version=sdk_version)
    libfile = extract(d, LIBNAME)
