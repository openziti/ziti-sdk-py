# Ziti SDK for Python

## Installation

Ziti SDK for Python is distributed via Python Package Index(PyPI)

```shell
pip install openziti
```

## Usage

### Identity Enrollment

Acquire [Ziti Enrollment Token](https://openziti.github.io/ziti/identities/overview.html)

```shell
python -m openziti enroll -j <JWT file> -i <ID JSON file>
```

### Environment Variables

- `ZITI_IDENTITIES` is a semi-colon-separated list of file paths to Ziti identity configuration JSON files.
- You may increase the log level of the underlying C SDK by setting environment variable `ZITI_LOG=4` (`DEBUG`).

### Samples

We several Python SDK sample programs for clients and servers in [sample/README.md](sample/README.md).

## Getting Help

Please use these community resources for getting help. We use GitHub [issues](https://github.com/openziti/ziti-sdk-py/issues)
for tracking bugs and feature requests and have limited bandwidth to address them.

- Read the [docs](https://openziti.github.io/ziti/overview.html)
- Join our [Developer Community](https://openziti.org)
- Participate in discussion on [Discourse](https://openziti.discourse.group/)

Copyright&copy; 2018-2022. NetFoundry, Inc.
