# Ziti Requests
This example shows the use of Ziti monkey patching a standard socket, via the requests module, to intercept network 
connections using a Ziti overlay.

## Setup :wrench:
Refer to the [examples README](../README.md) for details on setting up your network, service, and obtaining an identity 
file.

### Install Python Requirements
If you haven't already installed them, you'll need the dependent libraries used in the examples.
  ```bash
  pip install -r ../requirements
  ```

## Running the Example :arrow_forward:
This example accepts one _optional_ input argument.
1. The intercept address to bind to (if none is provided, the `demo.service.ziti` service from the local demo network will be assumed)
```shell
python ziti-requests.py <address-of-service>
```
This example also requires the identity file for binding to the service to be provided in the `ZITI_IDENTITIES` 
environment variable.
```shell
export ZITI_IDENTITIES="/path/to/id.json"
```

## Testing the Example :clipboard:
An easy way to test this example is with the local demo bootstrap script.

### Example:
After starting up the demo network with `python demo-run.py` and starting the uvicorn server with `python ziti-uvicorn/ziti-uvicorn.py demo-server.json demo-service`...
```shell
export ZITI_IDENTITIES=demo-client.json
python ziti-requests.py demo.service.ziti
```

### Example Output:
Using the local `demo.service.ziti` service on port `80` here is what this would look like.
```shell
$ python ziti-requests.py demo.service.ziti
{'content-type': 'application/json', 'server': 'uvicorn', 'date': '...'}
{"status":"OK"}
```