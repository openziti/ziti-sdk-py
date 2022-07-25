# OpenZiti Python SDK in Action

## Sample Setup

See [the main README](../README.md) for general setup and environment details.

- install Python requirements

  ```bash
  cd ./sample
  pip install -r requirements
  ```

- get yourself a Ziti identity from [ZEDS](https://zeds.openziti.org)

  follow enrollment instructions from the site, or better yet enroll with openziti Python module

  ```bash
  python -m openziti enroll --jwt=<enrollment token file> --identity=<identity file>
  ```

  the following instructions assume that Ziti identity is stored in `id.json` file

- set `ZITI_IDENTITIES` environment variable to location of `id.json` file

  ```bash
  export ZITI_IDENTITIES=<path to id.json>
  ```

## Run Samples

All sample scripts use predefined services in [ZEDS](https://zeds.openziti.org)

### `flask-of-ziti/helloFlazk.py`

Shows the use of a decorator function to monkeypatch a Flask server.

### `h-ziti-p.py`

Shows the use of Ziti monkeypatching standard socket to intercept network connections
and using Ziti overlay.

### `http-get.py`

Monkeypatch `requests.get(url)` to fetch a Ziti service with HTTP.

### `ziti-echo-server.py`

Open a socket to listen on the overlay for a particular Ziti service and send all bytes received back to the sender.

### `ziti-http-server.py`

Monkeypatch `http.server` to listen for requests on the overlay. Respond to clients with a simple JSON document.

### `ziti-socket-sample.py`

Shows the use of _raw_ Ziti socket.

