# Ziti Socket
This example shows the use of a _raw_ ziti socket. Using a raw socket will enable you to add zero trust to an 
application that manages its own sockets. In an application where sockets are managed the decorator can't be used to 
easily "zitify" the application.

## Setup :wrench:
Refer to the [examples README](../README.md) for details on setting up your network, service, and obtaining an identity 
file.

### Install Python Requirements
If you haven't already installed them, you'll need the dependent libraries used in the examples.
  ```bash
  pip install -r ../requirements
  ```

## Running the Example :arrow_forward:
This example accepts two _optional_ input arguments.
1. The intercept address to bind to (if none is provided, the `httpbin.ziti` service from ZEDs will be assumed)
2. The intercept port to bind to (if none is provided, port `80` will be assumed)
```shell
python ziti-socket.py <address-of-service> <service-port>
```
This example also requires the identity file for binding to the service to be provided in the `ZITI_IDENTITIES` 
environment variable.
```shell
export ZITI_IDENTITIES="/path/to/id.json"
```

## Testing the Example :clipboard:
Probably the easiest way to test this example is with the [Flazk example](../flask-of-ziti). Once that server is spun 
up and ready to handle requests, we can run this example, sending a request to the flask server.

### Example:
After starting up the Flazk example...
```shell
python ziti-socket.py python.flask.ziti 80
```

### Example Output:
Using a service called `python.flask.ziti` on port `80` here is what this would look like.
```shell
$ python ziti-socket.py python.flask.ziti 80
Ziti SDK version = (b'0.31.5', b'ccbc692')
HTTP/1.1 200 OK
Content-Length: 49
Content-Type: text/html; charset=utf-8
Date: Mon, 10 Apr 2023 20:43:44 GMT
Server: waitress

{ "name":"Ziti", "message":"Have some JSON Ziti"}

```