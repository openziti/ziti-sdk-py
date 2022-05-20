OpenZiti Python SDK in Action
---------------

# Setup

- install Python requirements

  `pip install -r requirements`


- get yourself a Ziti identity from [ZEDS](https://zeds.openziti.org)

  follow enrollment instructions from the site.
  these instructions assume that Ziti identity is stored in `id.json` file
  
  _Enrollment with Python is coming soon_


- set `ZITI_IDENTITIES` environment variable to location of `id.json` file

  `export ZITI_IDENTITIES=<path to id.json>`

# Run Samples!
  All sample scripts use predefined services in [ZEDS](https://zeds.openziti.org)
  
## ziti-socket-sample.py
  Shows the use of _raw_ Ziti socket.
  
## h-ziti-p.py
  Shows the use of Ziti monkeypatching standard socket to intercept network connections 
  and using Ziti overlay.