#  Copyright (c) 2026.  NetFoundry Inc
#
#  SPDX-License-Identifier: Apache-2.0
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

"""``enroll_with_idp`` and ``login_with_token`` turn down bad arguments before they reach the native library.

No controller is involved: these run on any ziti version.
"""

import pytest

import openziti
from openziti import EnrollMode, ZitiContext

CONTROLLER = "https://127.0.0.1:1"  # never contacted: the arguments are checked first


def test_enroll_modes_are_the_native_ones():
    """``ziti_enroll_mode`` in ziti-sdk-c's ``enums.h``: none, cert, token."""
    assert {m.name: m.value for m in EnrollMode} == {"NONE": 0, "CERT": 1, "TOKEN": 2}


def test_enroll_with_idp_is_public():
    assert openziti.enroll_with_idp is openziti.zitilib.enroll_with_idp


@pytest.mark.parametrize("controller", [None, 5, b"https://127.0.0.1:1"])
def test_enroll_with_idp_requires_a_string_controller(controller):
    with pytest.raises(TypeError):
        openziti.enroll_with_idp(controller, EnrollMode.TOKEN, "token")


def test_enroll_with_idp_requires_a_controller():
    with pytest.raises(ValueError):
        openziti.enroll_with_idp("", EnrollMode.TOKEN, "token")


@pytest.mark.parametrize("mode", [3, -1, "token", None])
def test_enroll_with_idp_requires_a_known_mode(mode):
    with pytest.raises(ValueError):
        openziti.enroll_with_idp(CONTROLLER, mode, "token")


@pytest.mark.parametrize("idp", [5, b"token"])
def test_enroll_with_idp_requires_a_string_idp(idp):
    with pytest.raises(TypeError):
        openziti.enroll_with_idp(CONTROLLER, EnrollMode.TOKEN, idp)


def test_enroll_with_idp_accepts_a_mode_as_a_number_and_no_idp_for_mode_none():
    # a refused connection is the native library's answer: the arguments got that far
    with pytest.raises(RuntimeError):
        openziti.enroll_with_idp(CONTROLLER, 0)


@pytest.mark.parametrize("token", [None, 5, b"token"])
def test_login_with_token_requires_a_string(token):
    with pytest.raises(TypeError):
        ZitiContext(1).login_with_token(token)
