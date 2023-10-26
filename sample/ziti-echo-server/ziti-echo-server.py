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

import sys
import signal
import threading
import openziti

def signal_handler(signum, frame):
    print("\nCtrl-C detected. Exiting...")
    sys.exit(0)

def run(ziti_id, service):
    ztx = openziti.load(ziti_id)
    server = ztx.bind(service)
    server.listen()

    while True:
        print('beginning accept')
        conn, peer = server.accept()
        print(f'processing incoming client[{peer}]')
        with conn:
            count = 0
            while True:
                print('starting receive')
                data = conn.recv(1024)
                if not data:
                    print(f'client finished after sending {count} bytes')
                    break
                count += len(data)
                conn.sendall(data)
                print(f'received data from client. returning {len(data)} bytes of data now...')


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    # Create a separate thread to run the server so we can respond to ctrl-c when in 'accept'
    server_thread = threading.Thread(target=run, args=(sys.argv[1], sys.argv[2]))
    server_thread.start()

    # Wait for the server thread to complete or Ctrl-C to be detected
    server_thread.join()