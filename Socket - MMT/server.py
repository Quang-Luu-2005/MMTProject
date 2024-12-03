import socket
import threading

HOST = "127.0.0.1"  # Loopback IP address
SERVER_PORT = 65432
FORMAT = "utf-8"

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    try:
        msg = None
        while msg != "exit":
            data = conn.recv(1024).decode(FORMAT)
            if not data:
                continue
            msg = data.strip()
            print(f"Client {addr}: {msg}")

            if msg == "exit":
                print(f"Client {addr} disconnected with 'exit' message.")
                break

            if msg == "shutdown":
                print(f"Client {addr} requested server shutdown.")
                raise KeyboardInterrupt  

            conn.send("Message received\n".encode(FORMAT))

    except ConnectionResetError:
        print(f"Client {addr} disconnected unexpectedly.")
    finally:
        print(f"Closing connection to {addr}")
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, SERVER_PORT))
    server.listen()
    print(f"SERVER SIDE\nServer listening on {HOST}:{SERVER_PORT}")

    try:
        while True:
            print("Waiting for a new connection...")
            conn, addr = server.accept()
            
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
            print(f"Active connections: {threading.active_count() - 1}")

    except KeyboardInterrupt:
        print("\nServer interrupted by user.")
    finally:
        print("Shutting down the server...")
        server.close()
        print("Server closed.")

if __name__ == "__main__":
    start_server()
