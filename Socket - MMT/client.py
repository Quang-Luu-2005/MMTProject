import socket
import sys
import time

HOST = "127.0.0.1"  # Loopback IP address
SERVER_PORT = 65432
FORMAT = "utf-8"

print("CLIENT SIDE")

try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, SERVER_PORT))
    print("Connected to server:", client.getsockname())

    msg = None
    while msg != "exit":
        try:
            msg = input("Enter message (type 'exit' to disconnect): ")
            if not msg.strip():
                print("Empty message. Please enter valid text.")
                continue

            client.send((msg + '\n').encode(FORMAT))

            if msg == "exit":
                break

            response = client.recv(1024).decode(FORMAT).strip()
            print("Server:", response)

        except KeyboardInterrupt:
            print("\nClient interrupted by user.")
            client.send("shutdown\n".encode(FORMAT)) 
            break

except ConnectionRefusedError:
    print("Could not connect to server. Exiting in 3 seconds...")
    time.sleep(3)
    sys.exit()

finally:
    print("Closing connection...")
    client.close()
    print("Connection closed.")
