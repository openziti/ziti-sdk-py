# Ziti Urllib3
This example shows using a "zitified" urllib3 module to send a request to a server.

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
1. The intercept address to bind to (if none is provided, the `httpbin.ziti` service from ZEDs will be assumed)
```shell
python ziti-urllib3.py <address-of-service>
```
This example also requires the identity file for binding to the service to be provided in the `ZITI_IDENTITIES` 
environment variable.
```shell
export ZITI_IDENTITIES="/path/to/id.json"
```

## Testing the Example :clipboard:
One easy way to test this example is with the [Flazk example](../flask-of-ziti). Once that server is spun up and ready 
to handle requests, we can run this example, sending a request to the flask server.

### Example:
After starting up the Flazk example with a service called `python.flask.ziti`...
```shell
export ZITI_IDENTITIES=<path/to/dialer/id.json>
python ziti-urllib3.py python.flask.ziti
```

### Example Output:
Using a service called `python.flask.ziti` on port `80` here is what this would look like.
```shell
$ python ziti-urllib3.py python.flask.ziti
200 OK
Have some Ziti!
```