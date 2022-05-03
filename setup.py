import setuptools
from setuptools import setup

setup(
    name='openziti',
    version='0.1.0',
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