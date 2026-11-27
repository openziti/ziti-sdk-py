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

"""``python -m openziti enroll``: the token file it always took, and enrollment with an external IdP.

The options are checked in process, with ``enroll`` and ``enroll_with_idp`` replaced. The tests that need a
controller run the command as the user does, against the quickstart controller and the in-process OIDC provider.
"""

import json
import queue
import re
import subprocess
import sys
import threading

import pytest

import openziti
from openziti import EnrollMode, ZitiContext
from openziti import __main__ as cli
from .ext_jwt_test import browse, wait_for_auth
from .util import identities_of

needs_ziti2 = pytest.mark.require_ziti(">=2.0.0")

IDENTITY = '{"ztAPI": "https://127.0.0.1:1280", "id": {"ca": "pem:ca"}}'


def usage_error(argv, capsys):
    """Run the command, expect that argparse turns the arguments down, and return what it says."""
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    assert exc.value.code == 2
    return capsys.readouterr().err


@pytest.fixture
def fake_idp_enroll(monkeypatch):
    """Replace ``enroll_with_idp``: the calls it gets are in ``calls``, as ``(args, kwargs)``."""
    calls = []

    def enroll_with_idp(*args, **kwargs):
        calls.append((args, kwargs))
        return IDENTITY

    monkeypatch.setattr(cli.zitilib, "enroll_with_idp", enroll_with_idp)
    return calls


def test_a_token_file_is_enrolled_as_it_always_was(monkeypatch, tmp_path):
    jwt, out = tmp_path / "enroll.jwt", tmp_path / "identity.json"
    jwt.write_text("the-jwt")
    calls = []
    monkeypatch.setattr(cli.zitilib, "enroll", lambda token, key=None, cert=None: calls.append((token, key, cert)) or IDENTITY)

    cli.main(["enroll", "-j", str(jwt), "-i", str(out), "-k", "key.pem", "-c", "cert.pem"])

    assert calls == [("the-jwt", "key.pem", "cert.pem")]
    assert out.read_text() == IDENTITY


def test_enroll_needs_a_token_file_or_a_controller(capsys):
    assert "required" in usage_error(["enroll", "-i", "identity.json"], capsys)


def test_enroll_takes_a_token_file_or_a_controller_not_both(capsys):
    err = usage_error(["enroll", "-j", "enroll.jwt", "--controller", "https://ctrl", "--mode", "token",
                       "-i", "identity.json"], capsys)
    assert "not allowed with" in err


def test_a_controller_needs_a_mode(capsys):
    assert "--mode" in usage_error(["enroll", "--controller", "https://ctrl", "-i", "identity.json"], capsys)


def test_mode_must_be_one_the_sdk_has(capsys):
    err = usage_error(["enroll", "--controller", "https://ctrl", "--mode", "bogus", "-i", "identity.json"], capsys)
    assert "invalid choice" in err


def test_mode_none_has_no_idp(capsys):
    err = usage_error(["enroll", "--controller", "https://ctrl", "--mode", "none", "--idp", "token",
                       "-i", "identity.json"], capsys)
    assert "--idp" in err


@pytest.mark.parametrize("option", ["--key", "--cert"])
def test_key_and_cert_are_for_a_token_file(option, capsys):
    err = usage_error(["enroll", "--controller", "https://ctrl", "--mode", "token", option, "x.pem",
                       "-i", "identity.json"], capsys)
    assert option in err and "--jwt" in err


@pytest.mark.parametrize("options", [["--mode", "token"], ["--idp", "token"], ["--timeout", "5"]])
def test_idp_options_are_for_a_controller(options, capsys):
    err = usage_error(["enroll", "-j", "enroll.jwt", "-i", "identity.json", *options], capsys)
    assert "--controller" in err


@pytest.mark.parametrize("mode", ["none", "cert", "token"])
def test_a_controller_is_enrolled_with_the_mode(mode, fake_idp_enroll, tmp_path):
    out = tmp_path / "identity.json"
    idp = [] if mode == "none" else ["--idp", "a-token"]

    cli.main(["enroll", "--controller", "https://ctrl", "--mode", mode, *idp, "-i", str(out)])

    [(args, kwargs)] = fake_idp_enroll
    assert args == ("https://ctrl", EnrollMode[mode.upper()], None if mode == "none" else "a-token")
    assert "timeout" not in kwargs  # the SDK's own default
    assert out.read_text() == IDENTITY


def test_the_login_timeout_is_handed_on(fake_idp_enroll, tmp_path):
    cli.main(["enroll", "--controller", "https://ctrl", "--mode", "token", "--idp", "signer", "--timeout", "12.5",
              "-i", str(tmp_path / "identity.json")])

    [(_, kwargs)] = fake_idp_enroll
    assert kwargs["timeout"] == 12.5


def test_the_login_url_is_told_to_the_user_on_stderr(monkeypatch, capsys, tmp_path):
    def enroll_with_idp(controller, mode, idp, on_login_url, **kwargs):
        on_login_url("https://idp.example.com/authorize?client_id=x")
        return IDENTITY

    monkeypatch.setattr(cli.zitilib, "enroll_with_idp", enroll_with_idp)

    cli.main(["enroll", "--controller", "https://ctrl", "--mode", "token", "-i", str(tmp_path / "identity.json")])

    captured = capsys.readouterr()
    assert "https://idp.example.com/authorize?client_id=x" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize("error", [RuntimeError("invalid state"), TimeoutError("no login")])
def test_a_failed_enrollment_exits_with_its_reason_and_writes_no_identity(error, monkeypatch, tmp_path):
    def enroll_with_idp(*args, **kwargs):
        raise error

    monkeypatch.setattr(cli.zitilib, "enroll_with_idp", enroll_with_idp)
    out = tmp_path / "identity.json"

    with pytest.raises(SystemExit) as exc:
        cli.main(["enroll", "--controller", "https://ctrl", "--mode", "token", "--idp", "signer", "-i", str(out)])

    assert exc.value.code == f"enroll failed: {error}"
    assert not out.exists()


def test_without_a_subcommand_it_prints_the_help(capsys):
    cli.main([])

    assert "usage: openziti" in capsys.readouterr().out


def test_version_prints_the_version(capsys):
    cli.main(["version"])

    assert capsys.readouterr().out.strip() == openziti.__version__


def openziti_enroll(*args):
    return [sys.executable, "-m", "openziti", "enroll", *args]


def stderr_lines(proc):
    """The lines the process writes to stderr, as they come, until it closes it."""
    lines = queue.Queue()

    def drain():
        for line in proc.stderr:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=drain, daemon=True).start()
    return lines


def login_url_of(lines, timeout=30):
    """The url the command tells the user to open: the one line of its output that is a url."""
    while True:
        line = lines.get(timeout=timeout)
        if line is None:
            pytest.fail("the command ended without a login url")
        if re.fullmatch(r"https?://\S+", line.strip()):
            return line.strip()


def token_of(idp, user):
    return idp.password_grant(user)["access_token"]


@needs_ziti2
def test_enroll_to_token_with_a_token_then_log_in(network_jwt, idp, idp_signer, idp_user, enroll_mode, tmp_path):
    enroll_mode("token")
    out = tmp_path / "identity.json"
    token = token_of(idp, idp_user)

    done = subprocess.run(openziti_enroll("--controller", network_jwt, "--mode", "token", "--idp", token,
                                          "-i", str(out)), capture_output=True, text=True, timeout=60)

    assert done.returncode == 0, done.stderr
    assert len(identities_of(idp_user)) == 1
    id_cfg = json.loads(out.read_text())["id"]
    assert id_cfg.get("ca") and not id_cfg.get("cert")

    # the file is what the SDK loads: the token is the login
    ztx, err = openziti.load(str(out))
    assert err == ZitiContext.EXTERNAL_LOGIN_REQUIRED, openziti.strerror(err)
    ztx.login_with_token(token_of(idp, idp_user))
    rc = wait_for_auth(ztx, 30)
    assert rc == 0, openziti.strerror(rc)


@needs_ziti2
def test_enroll_to_cert_with_a_token(network_jwt, idp, idp_signer, idp_user, enroll_mode, tmp_path):
    enroll_mode("cert")
    out = tmp_path / "identity.json"

    done = subprocess.run(openziti_enroll("--controller", network_jwt, "--mode", "cert",
                                          "--idp", token_of(idp, idp_user), "-i", str(out)),
                          capture_output=True, text=True, timeout=60)

    assert done.returncode == 0, done.stderr
    id_cfg = json.loads(out.read_text())["id"]
    assert id_cfg.get("cert") and id_cfg.get("key")
    ztx, err = openziti.load(str(out))
    assert err == 0, openziti.strerror(err)  # the cert is the login


@needs_ziti2
def test_enroll_none_writes_the_bootstrap_config(network_jwt, tmp_path):
    out = tmp_path / "bootstrap.json"

    done = subprocess.run(openziti_enroll("--controller", network_jwt, "--mode", "none", "-i", str(out)),
                          capture_output=True, text=True, timeout=60)

    assert done.returncode == 0, done.stderr
    id_cfg = json.loads(out.read_text())["id"]
    assert id_cfg.get("ca") and not id_cfg.get("cert") and not id_cfg.get("key")


@needs_ziti2
def test_enroll_with_a_signer_prints_the_login_url_and_waits_for_the_login(network_jwt, idp, idp_signer, idp_user,
                                                                            enroll_mode, tmp_path):
    enroll_mode("token")
    out = tmp_path / "identity.json"
    proc = subprocess.Popen(openziti_enroll("--controller", network_jwt, "--mode", "token", "--idp", idp_signer,
                                            "--timeout", "30", "-i", str(out)),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        url = login_url_of(stderr_lines(proc))
        assert url.startswith(f"{idp.issuer}/authorize")
        assert not out.exists()  # nothing to write before the user has logged in

        browse(idp, url, idp_user)

        assert proc.wait(timeout=30) == 0
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.stderr.close()
    assert len(identities_of(idp_user)) == 1
    assert json.loads(out.read_text())["id"].get("ca")


@needs_ziti2
def test_enroll_with_an_unknown_signer_fails_and_writes_nothing(network_jwt, idp_signer, enroll_mode, tmp_path):
    enroll_mode("token")
    out = tmp_path / "identity.json"

    done = subprocess.run(openziti_enroll("--controller", network_jwt, "--mode", "token", "--idp", "no-such-signer",
                                          "-i", str(out)), capture_output=True, text=True, timeout=60)

    assert done.returncode == 1
    assert "enroll failed" in done.stderr
    assert not out.exists()
