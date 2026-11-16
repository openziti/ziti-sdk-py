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

"""What ``openziti.monkeypatch()`` patches, and that leaving its ``with`` block gives all of it back."""

import socket

import pytest

import openziti


def patched_names():
    return socket.socket, socket.create_connection, socket.getaddrinfo


def test_monkeypatch_patches_inside_the_block_and_restores_after():
    orig = patched_names()
    with openziti.monkeypatch():
        assert all(now is not before for now, before in zip(patched_names(), orig))
    assert patched_names() == orig


def test_monkeypatch_restores_after_an_error():
    orig = patched_names()
    with pytest.raises(ValueError):
        with openziti.monkeypatch():
            raise ValueError("boom")
    assert patched_names() == orig


def test_nested_monkeypatch_restores_each_level():
    orig = patched_names()
    with openziti.monkeypatch():
        outer = patched_names()
        with openziti.monkeypatch():
            pass
        assert patched_names() == outer
    assert patched_names() == orig


def test_zitify_restores_after_the_call():
    orig = patched_names()

    @openziti.zitify()
    def socket_class_in_use():
        return socket.socket

    assert socket_class_in_use() is not orig[0]
    assert patched_names() == orig
