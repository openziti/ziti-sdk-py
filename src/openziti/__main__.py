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

from . import zitilib


def do_enroll():
    with open(args.jwt) as jwt_file:  # pylint: disable=unspecified-encoding
        jwt = jwt_file.read()

    with open(args.identity, 'wb') as id_file:
        id_json = zitilib.enroll(jwt, key=args.key, cert=args.cert)
        id_file.write(bytes(id_json, 'utf-8'))

def show_version():
    from openziti._version import get_versions
    modver = get_versions()
    v = modver['version']
    if args.verbose:
        modrev = modver['full-revisionid']
        version = zitilib.version()
        ziti_ver = version.version.decode()
        ziti_rev = version.revision.decode()
        print(f'version: {v}@{modrev}')
        print(f'ziti:    {ziti_ver}@{ziti_rev}')
    else:
        print(v)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser('openziti')
    parser.set_defaults(func=parser.print_help)
    subcommands = parser.add_subparsers(help='sub-command help',
                                        dest='subcommand')

    enroll_cmd = subcommands.add_parser('enroll', help='enroll identity')
    enroll_cmd.add_argument('-j', '--jwt', required=True)
    enroll_cmd.add_argument('-i', '--identity', required=True)
    enroll_cmd.add_argument('-k', '--key')
    enroll_cmd.add_argument('-c', '--cert')
    enroll_cmd.set_defaults(func=do_enroll)

    version_cmd = subcommands.add_parser('version', help='show version')
    version_cmd.set_defaults(func=show_version)
    version_cmd.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
    else:
        args.func()
