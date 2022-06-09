import sys

import urllib3
import openziti

# to run this sample
# set ZITI_IDENTITIES environment variable to location of your Ziti identity file
#
# python http-get.py <url>
# url should be the intercept address of a ziti service
if __name__ == '__main__':
    openziti.monkeypatch()
    http = urllib3.PoolManager()
    r = http.request('GET', sys.argv[1])
    print("{0} {1}".format(r.status, r.reason))
    print(r.data.decode('utf-8'))

