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

import argparse
import sys

from . import zitilib


def check_enroll_args(args):
    """The rules that go across options, which argparse does not have: ``-j`` and ``--controller`` are two ways to enroll."""
    fail = args.enroll_parser.error
    if args.jwt is not None:
        for option, value in (('--mode', args.mode), ('--idp', args.idp), ('--timeout', args.timeout)):
            if value is not None:
                fail(f'{option} goes with --controller, not with --jwt')
        return
    if args.mode is None:
        fail('--controller needs --mode')
    if args.mode == 'none' and args.idp is not None:
        fail('--idp is not used with --mode none')
    for option, value in (('--key', args.key), ('--cert', args.cert)):
        if value is not None:
            fail(f'{option} goes with --jwt, not with --controller')


def print_login_url(url):
    print(f'Open this URL in a browser to log in:\n{url}', file=sys.stderr, flush=True)


def do_enroll(args):
    check_enroll_args(args)

    if args.jwt is not None:
        with open(args.jwt) as jwt_file:  # pylint: disable=unspecified-encoding
            jwt = jwt_file.read()

        with open(args.identity, 'wb') as id_file:
            id_json = zitilib.enroll(jwt, key=args.key, cert=args.cert)
            id_file.write(bytes(id_json, 'utf-8'))
        return

    # without --timeout the login waits as long as the SDK's default
    timeout = {} if args.timeout is None else {'timeout': args.timeout}
    try:
        id_json = zitilib.enroll_with_idp(args.controller, zitilib.EnrollMode[args.mode.upper()], args.idp,
                                          on_login_url=print_login_url, **timeout)
    except (RuntimeError, TimeoutError) as e:
        sys.exit(f'enroll failed: {e}')

    with open(args.identity, 'wb') as id_file:
        id_file.write(bytes(id_json, 'utf-8'))


def show_version(args):
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


def build_parser():
    parser = argparse.ArgumentParser('openziti')
    subcommands = parser.add_subparsers(help='sub-command help',
                                        dest='subcommand')

    enroll_cmd = subcommands.add_parser(
        'enroll', help='enroll identity',
        description='Enroll an identity with an enrollment token (--jwt), or, with controller 2.0 or later, with '
                    'an external identity provider that the controller trusts (--controller).')
    enroll_cmd.add_argument('-i', '--identity', required=True, help='file to write the identity to')
    how = enroll_cmd.add_mutually_exclusive_group(required=True)
    how.add_argument('-j', '--jwt', help='file with the enrollment token')
    how.add_argument('--controller', help='controller URL, or the network JWT')
    enroll_cmd.add_argument('-k', '--key', help='private key for 3rd party CA enrollment (with --jwt)')
    enroll_cmd.add_argument('-c', '--cert', help='certificate for 3rd party CA enrollment (with --jwt)')
    enroll_cmd.add_argument('--mode', choices=[m.name.lower() for m in zitilib.EnrollMode],
                            help='what the controller does for the token: none (the identity exists already, '
                                 'the result is the bootstrap config), cert (signs a certificate request) or '
                                 'token (creates the identity, the token is its login)')
    enroll_cmd.add_argument('--idp', help='a token of the identity provider, or the name of its ext-jwt-signer to '
                                          'log in with in a browser. Without it, the first signer that offers '
                                          'the mode')
    enroll_cmd.add_argument('--timeout', type=float,
                            help='how long to wait for the login in a browser, in seconds (default: 300)')
    enroll_cmd.set_defaults(func=do_enroll, enroll_parser=enroll_cmd)

    version_cmd = subcommands.add_parser('version', help='show version')
    version_cmd.set_defaults(func=show_version)
    version_cmd.add_argument('-v', '--verbose', action='store_true')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.subcommand is None:
        parser.print_help()
    else:
        args.func(args)


if __name__ == '__main__':
    main()
