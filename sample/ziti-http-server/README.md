# Ziti HTTP Server
This example shows how to listen for HTTP requests on a service

## Setup :wrench:
Refer to the [examples README](../README.md) for details on setting up your network, service, and obtaining an identity 
file.

### Install Python Requirements
If you haven't already installed them, you'll need the dependent libraries used in the examples.
  ```bash
  pip install -r ../requirements
  ```

## Running the Example :arrow_forward:
We can test this example with `curl` however, in order to connect to the service over netcat you'll need an [identity](https://docs.openziti.io/docs/learn/core-concepts/identities/overview) 
and a tunneler for the device running the curl command. An easy way to set this up is to create an identity that has 
dial access on the intended service. Then run a [tunneler](https://docs.openziti.io/docs/reference/tunnelers/) on your 
platform, and enroll the identity.

### Example:
```shell
curl <name-of-service>
Hello!
```

### Example Output:
Using a service called `python.http.ziti` on port `80` here is what this would look like.
```shell
$ curl http://python.http.ziti:80
{"msg": "Help! I was zitified!"}
```
And on the `ziti-http-server` side, we can see the following output showing the identity (`desktop.user`) and some 
request metadata.
```
desktop.user - - [12/Apr/2023 15:03:33] "GET / HTTP/1.1" 200 -
```