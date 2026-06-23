# Ziti Uvicorn
This example shows how to run an ASGI application (using FastAPI) served via Uvicorn listening directly on the OpenZiti network.

By overriding Uvicorn's server and configuration binders, the web server can bind to and accept secure incoming connections from clients on the OpenZiti overlay network without exposing any public TCP ports.

## Setup :wrench:
Refer to the [examples README](../README.md) for details on setting up your network, service, and obtaining an identity file.

### Install Python Requirements
If you haven't already installed them, you'll need the dependent libraries used in the examples.
  ```bash
  pip install -r ../requirements.txt
  ```

## Running the Example :arrow_forward:
This example requires two input arguments:
1. The identity file to load (`demo-server.json` if running the demo bootstrap script)
2. The service name to bind to (`demo-service` if running the demo bootstrap script)

```shell
python ziti-uvicorn.py <path/to/identity.json> <service-name>
```

### Example:
After booting up your OpenZiti network (e.g., using `python demo-run.py`):
```shell
python ziti-uvicorn.py demo-server.json demo-service
```

## Testing the Example :clipboard:
You can test connecting to this uvicorn server using any of the client examples on the dialer side (e.g., [Ziti Requests](../ziti-requests) or [Ziti urllib3](../ziti-urllib3)) targeting the service's intercept address.

### Example with Ziti Requests:
1. On the dialer client machine/terminal, set the dialer identity environment variable:
   ```shell
   export ZITI_IDENTITIES=demo-client.json
   ```
2. Run the requests client:
   ```shell
   python ../ziti-requests/ziti-requests.py demo.service.ziti
   ```

### Example Output:
```shell
$ python ../ziti-requests/ziti-requests.py demo.service.ziti
requesting http://demo.service.ziti/
{'content-type': 'application/json', 'server': 'uvicorn', 'date': '...'}
{"status":"OK"}
```
