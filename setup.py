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

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='openziti',
    version=versioneer.get_version(),
    description='Ziti Python SDK',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/openziti/ziti-sdk-py',
    project_urls={
    'Documentation': 'https://openziti.github.io/ziti/overview.html',
    'Source': 'https://github.com/openziti/ziti-sdk-py',
    'Tracker': 'https://github.com/openziti/ziti-sdk-py/issues',
    'Discussion': 'https://openziti.discourse.group/',
    },
    author='Eugene Kobyakov',
    author_email='eugene@openziti.org',
    license='Apache 2.0',
    packages=['ziti'],
    install_requires=[],
    include_package_data=True,
    package_data={
        "ziti": ["lib/*"],
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