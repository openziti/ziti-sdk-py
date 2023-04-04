# Hello Flazk <img align="right" src="../../images/python-flask-text.png" width="20%">
This example shows the simplicity in integrating zero trust into a web server or API using Flask. This example also 
shows how to use the decorator to apply the monkeypatch.

This is a perfect example of application to application embedded zero trust. When used in conjunction with the 
[HTTP GET](../http-get) example, both ends of the network are fully app-embedded zero trust applications and therefore 
offer complete encryption from app to app, no unencrypted data ever leaves the application environment.
![ztaa-model-flazk.png](..%2F..%2Fimages%2Fztaa-model-flazk.png)

## Setup :wrench:
Refer to the [Examples README](../README.md) for details on setting up your network, service, and obtaining an identity 
file.

## Running the Example :arrow_forward:
This example accepts two input arguments. 
1. The identity file to be used by the SDK tunneler
2. The service to bind to
```shell
python helloFlazk.py </path/to/id.json> <name-of-service>
```

## Testing the Example :clipboard:
By default, the base url is mapped to our `hello_world()` function. So, if we hit that endpoint we will see the 
response from the function which is simply `Have some ziti`. This could be tested with 
1. The [HTTP GET](../http-get) example
2. A curl command

       curl <name-of-service>:<intercept-port>
3. Or simply visiting the intercept address in a browser.