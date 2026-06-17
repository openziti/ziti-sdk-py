import logging

import pytest_asyncio

import openziti

logger = logging.getLogger()

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
    r,w = await ztx.open_connection(ziti_setup["service"])
    w.write(b"hello")
    await w.drain()
    resp = await r.read(1024)
    assert resp == b"hello"
    w.close()

