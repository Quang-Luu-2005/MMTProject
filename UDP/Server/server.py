import socket
import os

HOST = "127.0.0.1"  # Loopback IP address
PORT = 65432
BUFFER_SIZE = 1024
FORMAT = "utf-8"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Server directory

# Update list.txt with files in the Server directory
def update_file_list():
    files = [f for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))]
    with open(os.path.join(BASE_DIR, "list.txt"), "w") as f:
        for file in files:
            if file not in ["server.py", "list.txt"]:
                f.write(file + "\n")

# Send a file to the client
def send_file(conn, file_name):
    file_path = os.path.join(BASE_DIR, file_name)
    if not os.path.exists(file_path):
        conn.send("ERROR: File not found.\n".encode(FORMAT))
        return
    
    file_size = os.path.getsize(file_path)
    conn.send(f"OK:{file_size}\n".encode(FORMAT))  # Notify client about file size

    with open(file_path, "rb") as f:
        while chunk := f.read(BUFFER_SIZE):
            conn.send(chunk)
    print(f"[SENT] {file_name} to client.")

def main():
    update_file_list()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            print(f"[NEW CONNECTION] {addr} connected.")
            try:
                while True:
                    file_name = conn.recv(BUFFER_SIZE).decode(FORMAT).strip()
                    if not file_name:
                        break
                    print(f"[REQUEST] Client requested file: {file_name}")
                    send_file(conn, file_name)
            except ConnectionResetError:
                print(f"[DISCONNECTED] Client {addr} disconnected unexpectedly.")
            finally:
                conn.close()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
