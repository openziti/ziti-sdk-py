import logging

import pytest
import pytest_asyncio
from requests import request

import openziti

logger = logging.getLogger()


@pytest.mark.skip(reason="c-sdk connects immediately even if service not available (ECONNRESET is issued later)")
def test_connect_timeout(echo_server_process, ziti_setup):
    clt_id = ziti_setup["client"]
    (ztx, rc) = openziti.load(clt_id)
    assert rc == 0
    with pytest.raises(TimeoutError):
        ztx.connect(ziti_setup["service"], timeout=0.001)


def test_echo(echo_server_process, ziti_setup):
    clt_id = ziti_setup["client"]
    print("connecting with identity ", clt_id)
    (ztx, rc) = openziti.load(clt_id)
    assert rc == 0

    with ztx.connect(ziti_setup["service"]) as sock:
        sock.setblocking(True)
        sock.send(b"hello")
        resp = sock.recv(1024)
        assert resp == b"hello"


async def test_open_connection(echo_server_process, ziti_setup):
    clt_id = ziti_setup["client"]
    print("connecting with identity ", clt_id)
    (ztx, rc) = openziti.load(clt_id)
    assert rc == 0
    r, w = await ztx.open_connection(ziti_setup["service"])
    w.write(b"hello")
    await w.drain()
    resp = await r.read(1024)
    assert resp == b"hello"
    w.close()


def test_uvicorn(uvicorn_process, ziti_setup):
    clt_id = ziti_setup["client"]
    intercept = ziti_setup["intercept"]
    address = f"http://{intercept['addresses'][0]}:{intercept['portRanges'][0]['low']}"

    ztx, err = openziti.load(clt_id, 5000)
    assert err == 0, f"failed to load identity: {openziti.strerror(err)}"

    with openziti.monkeypatch():
        resp = request("GET", address)
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["status"] == "OK"
