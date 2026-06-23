# Python SDK for OpenZiti Examples

## Setup

You will need an OpenZiti network to use the examples. If you don't already have one running, you can easily spin up a local development network using our bootstrap demo script:

```bash
python demo-run.py
```

This script will start a local controller and router using the `ziti` CLI (which must be installed in your `PATH`), configure the `demo-service` (intercepting `demo.service.ziti:80`), and enroll two local test identities: `demo-client.json` and `demo-server.json`.

Alternatively, you can follow our [express install guides](https://docs.openziti.io/docs/learn/quickstarts/network/) to set up a custom network, or try cloud Ziti for free (check out more [here](https://docs.openziti.io/)).

### Installing the SDK

The Python SDK for OpenZiti is distributed via the Python Package Index (PyPI) and can be installed using
[`pip`](https://pypi.org/project/openziti/) package manager.

```shell
pip install openziti
```

### Install Python Requirements

First, you'll need the dependent libraries used in the examples.

  ```bash
  cd ./sample
  pip install -r requirements
  ```

### Get and Enroll an Identity

You need an [identity](https://docs.openziti.io/docs/learn/core-concepts/identities/overview) to be used by the example 
application. If you ran `python demo-run.py`, the required identities (`demo-client.json` and `demo-server.json`) are automatically created and enrolled for you in the current directory.

Otherwise, you can find all the information you need for creating and enrolling an identity in the [doc here](https://docs.openziti.io/docs/learn/core-concepts/identities/overview#creating-an-identity).

Alternatively, if you have an identity enrollment token (JWT file), you can perform the enrollment with the Python SDK.

  ```bash
  python -m openziti enroll --jwt=</path/to/enrollment-token-file.jwt> --identity=</path/to/id.json>
  ```

### Environment

The `ZITI_IDENTITIES` environment variable can be used to store the paths to any identity files you have. If you have 
more than one identity file, you can use the `;` operator as a delimiter to provide additional identities.

  ```bash
  export ZITI_IDENTITIES=</path/to/id.json>
  ```

There is an optional environment variable `ZITI_LOG` which, by default is set to `1`. This value can be adjusted to 
output more or less log information. A `ZITI_LOG` level of `6` will output `TRACE` level logs.

### Network

Your network overlay needs to have a [Service](https://docs.openziti.io/docs/learn/core-concepts/services/overview), 
and the proper [Service Configurations](https://docs.openziti.io/docs/learn/core-concepts/config-store/overview), the 
documentation for which is linked.

## Examples

> **Note**
> The example scripts are configured to use the local `demo.service.ziti` service by default, which can be easily spun up using `python demo-run.py`.

### [Flazk](flask-of-ziti) <img src="../images/python-flask.jpg" width="2%">

An example showing the simplicity in integrating zero trust into a web server or API using Flask. This example also 
shows how to use the decorator to apply the monkeypatch.
`flask-of-ziti/helloFlazk.py`

### [Ziti Echo Server](ziti-echo-server)

An example showing how to open a socket to listen on the network overlay for a particular service and send all bytes 
received back to the sender.

### [Ziti HTTP Server](ziti-http-server)

An example showing how to monkeypatch `http.server` to listen for HTTP requests on the network overlay. When a request 
is captured, a response with a simple JSON document is sent to clients.

### [Ziti Requests](ziti-requests)

An example showing the use of Ziti monkey patching a standard socket, via the requests module, to intercept network 
connections using Ziti overlay.

### [Ziti Socket](ziti-socket)

An example showing the use of a _raw_ Ziti socket.

### [Ziti urllib3](ziti-urllib3)

An example showing how to monkeypatch `urllib3` to fetch a Ziti service using HTTP.

### [Ziti Uvicorn](ziti-uvicorn)

An example showing how to run a FastAPI ASGI application served via Uvicorn listening directly on the OpenZiti network.

### [S3 Log Uploader](sample/s3z)

Upload some log files to a private S3 bucket via the Ziti with the boto3 SDK.
