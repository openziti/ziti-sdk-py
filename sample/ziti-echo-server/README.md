# Ziti Echo Server
This example shows how to open a socket to listen on the network overlay for a particular service and send all bytes 
received back to the sender.

## Setup :wrench:
Refer to the [examples README](../README.md) for details on setting up your network, service, and obtaining an identity 
file.

### Install Python Requirements
If you haven't already installed them, you'll need the dependent libraries used in the examples.
  ```bash
  pip install -r ../requirements
  ```

## Running the Example :arrow_forward:
This example accepts two input arguments. 
1. The identity file to be used by the SDK tunneler to bind to the service
2. The service to bind to
```shell
python ziti-echo-server.py </path/to/id.json> <name-of-service>
```

## Testing the Example :clipboard:
Netcat can be used to test this however, in order to connect to the service over netcat you'll need an [identity](https://docs.openziti.io/docs/learn/core-concepts/identities/overview) 
and a tunneler for the device running the netcat commands. An easy way to set this up is to create an identity that has 
dial access on the intended service. Then run a [tunneler](https://docs.openziti.io/docs/reference/tunnelers/) on your 
platform, and enroll the identity.

If we use netcat to connect to the intercept address and send some data, we will see a response of the exact same data 
we sent (hence the name, echo server).

### Example:
```shell
nc <name-of-service> <intercept-port>
Hello!
```

### Example Output:
Using a service called `python.echo.ziti` on port `80` here is what this would look like.
```shell
nc python.echo.ziti 80
Hello
Hello
```