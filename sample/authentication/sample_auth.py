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
import sys

import openziti
import zitilib
from openziti import ZitiContext

def auth(cfg: str) -> None:
    """
    Authenticate with Ziti Identity using the provided configuration file.
    this sample shows possible steps required to fully authenticate an OpenZiti Identity.
    """
    ztx, err = openziti.load(cfg)

    if err == ZitiContext.EXTERNAL_LOGIN_REQUIRED:
        signers = ztx.get_external_signers()
        for i, s in enumerate(signers):
            print(f"{i}: {s}")
        print(f"select external signer [0-{len(signers)-1}]: ", end="")

        idx = int(input())
        signer = signers[idx]
        url = ztx.login_external(signer)
        print(f"continue in browser")
        import webbrowser
        webbrowser.open(url, new=2, autoraise=True)
        err = ztx.wait_for_auth()
        print("wait_for_auth returned", err)

    if err == ZitiContext.PARTIALLY_AUTHENTICATED:
        print("enter TOTP code: ", end="")
        totp = input()
        try:
            ztx.login_totp(totp)
            err = 0
        except Exception as e:
            print(f"Failed to login with TOTP: {e}")
            return

    if err == 0:
        print("Authentication successful")
        print(f"Ziti version: {openziti.version()}")
    else:
        print(f"Authentication failed with error code: {err}/{zitilib.errorstr(err)}")

if __name__ == '__main__':
    cfg = sys.argv[1]
    auth(cfg)
