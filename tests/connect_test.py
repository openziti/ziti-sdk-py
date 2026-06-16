import logging
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




