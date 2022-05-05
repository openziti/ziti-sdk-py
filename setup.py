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

import setuptools
from setuptools import setup
import versioneer

setup(
    name='openziti',
    version=versioneer.get_version(),
    description='Ziti Python SDK',
    url='https://github.com/openziti/ziti-sdk-py',
    author='Eugene Kobyakov',
    author_email='eugene@openziti.org',
    license='Apache 2.0',
    packages=['ziti'],
    install_requires=[],
    include_package_data=True,
    package_data={
        "": ["libziti.so"],
    },
    ext_modules=[
        setuptools.Extension("zitilib", [])
    ],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)