#  Copyright NetFoundry Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
Sample demonstrating async HTTP client with OpenZiti integration.

This example shows how to use aiohttp (async HTTP client library) to make
non-blocking HTTP requests to services through an OpenZiti network.

Install dependencies with:
    pip install aiohttp
"""

import asyncio
import sys
from socket import socket
from typing import Any

from aiohttp import ThreadedResolver

import openziti
import aiohttp

identity = sys.argv[1]
url = sys.argv[2]


def socket_factory(addr_info) -> socket:
    family, type_, proto, _, _ = addr_info
    sock = openziti.socket(family=family, type=type_, proto=proto)
    return sock


class ZitiResolver(ThreadedResolver):
    """Custom resolver that uses OpenZiti for DNS resolution."""

    async def resolve(self, host: str, port: int = 0, family: int = 0) -> list:
        loop = asyncio.get_running_loop()
        addrs = await loop.run_in_executor(None, openziti.getaddrinfo, host, port, family, 0, 0, 0)
        return [dict(
                    hostname=host,
                    host=a[4][0],
                    port=a[4][1],
                    family=a[0],
                    proto=a[3],
                    flags=0,
                ) for a in addrs]


def ziti_connector() -> aiohttp.TCPConnector:
    """Creates a Ziti connector."""
    return aiohttp.TCPConnector(socket_factory=socket_factory, resolver=ZitiResolver())


async def fetch(session: aiohttp.ClientSession, url: str):
    """
    Asynchronously fetch data from a URL via Ziti.
    
    Args:
        session: aiohttp ClientSession
        url: The URL to fetch
        
    Returns:
        response status
    """
    try:
        print(f"Fetching: {url}")
        async with session.get(url) as response:
            print(f"{url} -> {response.status} {response.reason}")
            if response.status == 200:
                return f"✓ Success: {url} (Status: {response.status})"
            else:
                return {"error": f"HTTP {response.status}"}
    except asyncio.TimeoutError:
        print(f"✗ Timeout: {url}")
        return {"error": "Request timeout"}
    except aiohttp.ClientError as e:
        print(f"✗ Connection error: {url} - {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"✗ Unexpected error: {url} - {e}")
        return {"error": str(e)}

async def concurrent_requests(urls: list) -> tuple[BaseException | Any]:
    """
    Execute multiple concurrent HTTP requests.
    
    Args:
        urls: List of URLs to fetch

    Returns:
        List of results from all requests
    """
    with ziti_connector() as connector:
        async with aiohttp.ClientSession(connector = connector) as session:
            tasks = [fetch(session, u) for u in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

async def main():
    """Main entry point for the async HTTP client sample."""

    # Example 1: Simple GET request for JSON
    print("=" * 50)
    print("Example 1: Single Request")
    print("=" * 50)
    with ziti_connector() as conn:
       async with aiohttp.ClientSession(connector=conn) as session:
           result = await fetch(session, url)
           print(f"Response: {result}...\n")

    # Example 2: Multiple concurrent GET requests
    print("=" * 50)
    print("Example 2: Multiple Concurrent Requests")
    print("=" * 50)
    urls = [url for _ in range(0, 10)]
    results = await concurrent_requests(urls)
    print(f"Completed {len(results)} requests\n")
    for result in results:
        print(f" >> {result}")

    # Cleanup
    print("Done!")


if __name__ == '__main__':
    print(f"Ziti SDK version = {openziti.version()}\n")
    # Load Ziti identity if provided
    ztx, err = openziti.load(sys.argv[1])
    print(f"Loaded Ziti Identity from {sys.argv[1]} with error code {err}\n")
    asyncio.run(main())
    openziti.shutdown()

