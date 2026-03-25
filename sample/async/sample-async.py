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
Sample demonstrating asynchronous connection to a Ziti service using asyncio.

This example shows how to use Python's asyncio library to establish non-blocking
connections to services through an OpenZiti network. The sample connects to a
remote service and performs async I/O operations.
"""

import asyncio
import sys
import openziti
from socket import SOCK_STREAM, SHUT_WR

identity = sys.argv[1]
hostname, port  = sys.argv[2].split(':')

async def fetch_data_async(service_address: str, p: int, request: str) -> str:
    """
    Asynchronously connect to a Ziti service and fetch data.
    
    Args:
        service_address: intercept address
        p: The port to connect to
        request: The HTTP request or data to send
        
    Returns:
        The response data as a string
    """
    try:
        ssl = None
        if p == 443:
            ssl = True
        r,w = await openziti.open_connection(service_address, p, ssl=ssl)
        print(f"Connected to {service_address}:{p}")
        
        # Send the request
        request_bytes = request.encode('utf-8')
        w.write(request_bytes)
        await w.drain()
        print("Request sent")
        
        # Receive the response
        response_data = b''
        while True:
            try:
                chunk = await r.read(4096)
                if not chunk:
                    break
                response_data += chunk
            except Exception as e:
                print(f"Error receiving data: {e}")
                break
        
        w.close()

        return response_data.decode('utf-8', errors='ignore')
    
    except Exception as e:
        print(f"Error: {e}")
        return ""


async def multiple_requests(services: list) -> None:
    """
    Demonstrate making multiple concurrent requests to different services.
    
    Args:
        services: List of tuples (address, port, request)
    """
    tasks = []
    for address, p, request in services:
        task = fetch_data_async(address, int(p), request)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        if result:
            print(f"\n--- Response {i+1} ---")
            print(result[:500])  # Print first 500 chars
            if len(result) > 500:
                print("... (truncated)")


async def main():
    """Main entry point for the async sample."""
    print(f"Ziti SDK version = {openziti.version()}\n")
    # Example 1: Simple HTTP request to httpbin service through Ziti
    print("=== Example 1: Simple HTTP Request ===")
    http_request = """GET /json HTTP/1.1\r
Accept: */*\r
Connection: close\r
Host: httpbin.ziti\r
User-Agent: Ziti-AsyncIO-Sample\r
\r
"""
    
    # Execute Multiple concurrent requests
    print("\n=== Concurrent Requests ===")
    services = [ (hostname, 443, http_request) for i in range(0,10) ]

    try:
        await multiple_requests(services)
    except Exception as e:
        print(f"Example 2 failed: {e}")
    
    # Cleanup
    print("\nDone!")


if __name__ == '__main__':
    openziti.load(identity)
    asyncio.run(main())
    openziti.shutdown()
