import socket
import threading
import os
import hashlib

HOST = "127.0.0.1"
PORT = 65432
CHUNK_SIZE = 1024 * 1024  # 1MB
FORMAT = "utf-8"

FILE_LIST = "files.txt"

def calculate_checksum(filename):
    """Tính checksum MD5 của một file."""
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def send_file_chunk(conn, filename, offset):
    """Gửi một chunk từ file theo yêu cầu."""
    try:
        with open(filename, "rb") as f:
            f.seek(offset) 
            chunk = f.read(CHUNK_SIZE)
        conn.sendall(chunk) 
    except Exception as e:
        conn.sendall(b"ERROR: Failed to read file.")
        print(f"Error sending chunk: {e}")

def handle_client(conn, addr):
    """Xử lý yêu cầu từ một client."""
    print(f"Client {addr} connected.")
    try:
        while True:
            request = conn.recv(1024).decode(FORMAT).strip()
            if not request:
                break

            if request == "LIST":
                if not os.path.exists(FILE_LIST):
                    conn.sendall(b"ERROR: File list not found.")
                    continue
                
                with open(FILE_LIST, "r") as f:
                    file_list = f.read()
                conn.sendall(file_list.encode(FORMAT))
            
            else:
                try:
                    filename, offset = request.split()
                    offset = int(offset)
                    
                    if not os.path.exists(filename):
                        conn.sendall(b"ERROR: File not found.")
                    else:
                        send_file_chunk(conn, filename, offset)
                except Exception as e:
                    conn.sendall(b"ERROR: Invalid request format.")
                    print(f"Error processing request: {e}")
    except ConnectionResetError:
        print(f"Client {addr} disconnected unexpectedly.")
    finally:
        conn.close()
        print(f"Connection to {addr} closed.")

def start_server():
    """Khởi động server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()
        print("Server stopped.")

if __name__ == "__main__":
    start_server()
