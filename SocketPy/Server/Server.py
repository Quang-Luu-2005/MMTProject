import socket
import os
import threading

HOST = "127.0.0.1"
PORT = 65432
FORMAT = "utf-8"

# đọc lấy thông tin tên file, kích thước (theo BYTE)
def list_files():
    files = {}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "file_list.txt"), "r") as f:
        for line in f:
            name, size = line.strip().split()
            files[name] = size
    return files

def handle_client(conn, files):
    while True:
        try:
            data = conn.recv(1024).decode(FORMAT).strip()
            if not data:
                break

            request, *others = data.split()

            if request == "LIST": # get líst of files on server
                file_list = "\n".join(f"{name} {size}" for name, size in files.items())
                conn.send(file_list.encode(FORMAT))

            elif request == "DOWNLOAD": # download a file
                file_name, offset, chunk_size = others
                if os.path.exists(file_name):
                    print("Exist")
                offset = int(offset)
                chunk_size = int(chunk_size) 

                if file_name in files:
                    with open(file_name, "rb") as f:
                        f.seek(offset)
                        chunk_to_send = f.read(chunk_size)
                        conn.send(chunk_to_send)
                else:
                    conn.send(f"ERROR: {file_name} not found")

        except Exception as e:
            print(f"Error: {e}")
            break

    conn.close()

def start_server():
    files = list_files()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(30)
    print(f"Server listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(conn, files))
            client_handler.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()
        print("Server stopped.")

if __name__ == "__main__":
    start_server()
