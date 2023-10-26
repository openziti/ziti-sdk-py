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
import openziti
import socket

def netcat_client(ziti_id, service):
    try:
        zitiContext = openziti.load(ziti_id)
    except Exception as e:
        print(f'could not find identity file: {e}')
        return

    try:
        client = openziti.socket(type = socket.SOCK_STREAM) #socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 65535
        client.connect((service, port))
        print(f"Connected to {service}:there_is_no_port")

        while True:
            user_input = input("Enter a message: ")
            client.send(user_input.encode("utf-8") + b'\n')

            data = client.recv(1024)
            if len(data) == 0:
                break

            print("Server response:", data.decode("utf-8"))

    except ConnectionRefusedError:
        print(f"Connection to {service}:there_is_no_port refused.")
    except KeyboardInterrupt:
        print("\nConnection closed.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    netcat_client(sys.argv[1], sys.argv[2])