<a href="https://docs.openziti.io/">
    <img src="./images/ziti-logo-dark.svg" alt="ziti logo" title="OpenZiti" align="right" height="60" />
</a>

# Ziti SDK for Python
:star: Star us on GitHub!
<p align="center">
  <a href="https://openziti.discourse.group/">
    <img src="https://img.shields.io/discourse/users?server=https%3A%2F%2Fopenziti.discourse.group%2F" alt="Discourse">
  </a>
  <a href="https://pypi.org/project/openziti/">
    <img src="https://img.shields.io/pypi/dd/openziti" alt="Downloads">
  </a>
  <a href="https://opensource.org/licenses/Apache-2.0">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License">
  </a>
</p>

<p align="center">
  <a href="#getting-started">Getting Started</a> •
  <a href="#examples">Examples</a> •
  <a href="#support">Support</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

<img src="./images/Ziggy-Loves-Python.svg" align="right" alt="ziggy-loves-python" width="15%">

Ziti SDK for Python is a library that enables developers to integrate OpenZiti network connectivity into their Python 
applications. OpenZiti is an open-source project that provides secure, zero-trust networking for applications running 
on any platform. This SDK provides the tools to allow developers to establish secure connections with remote network 
resources over a Ziti network and simplifies the process of adding secure, zero-trust network connectivity built into 
your Python application.

Here is a model of Zero Trust  at the application level, giving you the most secure network connectivity possible. 
Traffic is encrypted and passed directly from app to app for the ultimate security.
<p align="center">
<img src="./images/ztaa-model-overview.png" alt="Zero-trust-application-access">
</p>

## Getting Started
If you don't already have a Ziti network running, you can follow our [express install guides](https://docs.openziti.io/docs/learn/quickstarts/network/) 
to set up the Ziti network that fits your needs. Or, you can try a NetFoundry hosted solution, check out more [here](https://docs.openziti.io/).

### Installing the SDK

Ziti SDK for Python is distributed via the Python Package Index (PyPI) and can be installed using [`pip`](https://pypi.org/project/openziti/).

```shell
pip install openziti
```

### Using Ziti Python SDK
With just a few lines of code, you can turn your plain old web server into a secure, zero-trust embedded application. 
Below is an example of just how little code it takes to get started.

Provide a hostname, and port for your application, a simple monkeypatch, and you're ready to go. You don't even need to 
know what a monkeypatch is!
```python
hostName = "127.0.0.1"
serverPort = 18080

cfg = dict(
    ztx=openziti.load('/Users/geoffberl/python.flask.json'),
    service="python.flask"
)
openziti.monkeypatch(bindings={(hostName, serverPort): cfg})
```
## Examples
Try it out yourself with one of our examples
* [Flask](./sample/flask-of-ziti)
* [HZTP](./sample/h-ziti-p.py)
* [HTTP GET](./sample/http-get.py)
* [Echo Server](./sample/ziti-echo-server.py)
* [HTTP Server](./sample/ziti-http-server.py)
* [Ziti Socket](./sample/ziti-socket-sample.py)

## Support
### Looking for Help?
Please use these community resources for getting help. We use GitHub [issues](https://github.com/openziti/ziti-sdk-py/issues)
for tracking bugs and feature requests and have limited bandwidth to address them.

- Read the [offical docs](https://docs.openziti.io/docs/learn/introduction/)
- Join our [Developer Community](https://openziti.org)
- Participate in discussion on [Discourse](https://openziti.discourse.group/)
## Contributing
Do you want to get your hands dirty and help make OpenZiti better? Contribute to the OpenZiti open-source project 
through bug reports, bug fixes, documentation, etc. Check out our guide on contributing to our projects [here](https://docs.openziti.io/policies/CONTRIBUTING.html).
## License
[Apache 2.0](./LICENSE)
