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

from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension

import versioneer

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

ZITI_SDK_BASE = 'https://github.com/openziti/ziti-sdk-c/releases/download'


class GetZitilib(build_ext):

    def build_extension(self, ext) -> None:
        import platform
        ziti_ver = self.get_sdk_version()
        osname = platform.system()
        sdk_distro = self.download_sdk(ziti_ver, osname, platform.machine())
        self.extract_zitilib(sdk_distro, self.get_lib_name(osname), self.build_lib)

    def get_lib_name(self, osname):
        osname = osname.capitalize()
        if osname == 'Linux':
            libname = 'libziti.so'
        elif osname == 'Darwin':
            libname = 'libziti.dylib'
        elif osname == 'Windows':
            libname = 'ziti.dll'
        else:
            raise RuntimeError(f"Unsupported platform[{osname}]")
        return libname

    def get_sdk_version(self):
        opts = self.distribution.get_option_dict('openziti')
        _, ver = opts['ziti_sdk_version']
        return ver

    def extract_zitilib(self, distro, libname, target):
        import zipfile
        from io import BytesIO
        with zipfile.ZipFile(BytesIO(distro)) as zipf:
            return zipf.extract(member=f'lib/{libname}', path=f'{target}/openziti')

    def download_sdk(self, version, osname, arch):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        filename = f'{ZITI_SDK_BASE}/{version}/ziti-sdk-{version}-{osname}-{arch}.zip'
        headers = {}
        req = Request(url=filename, headers=headers)
        try:
            with urlopen(req) as response:
                length = response.getheader('content-length')
                if response.status != 200:
                    raise Exception(f'Could not download "{filename}"')
                    return None

                print(f"Downloading {length} from {filename}")
                return response.read()
        except HTTPError:
            raise

class ZitilibExt(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])


cmds = dict(build_ext=GetZitilib)
cmds = versioneer.get_cmdclass(cmds)

setup(
    version=versioneer.get_version(),
    cmdclass=cmds,
    ext_modules=[
        ZitilibExt('_get_ziti_lib'),
    ],

    packages=['openziti'],
)