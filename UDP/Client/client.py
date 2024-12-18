import socket
import os
import time
import sys

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432
CHUNK_SIZE = 1024
FORMAT = "utf-8"
INPUT_FILE = os.path.join(os.path.dirname(__file__), "input.txt")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# Ensure the downloads directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_file(file_name):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            client.connect((SERVER_HOST, SERVER_PORT))
            client.send(file_name.encode(FORMAT))

            response = client.recv(CHUNK_SIZE).decode(FORMAT).strip()
            if response.startswith("ERROR"):
                print(f"[ERROR] {response}")
                return

            _, file_size = response.split(":")
            file_size = int(file_size)
            print(f"[INFO] Downloading {file_name} ({file_size} bytes)...")

            file_path = os.path.join(DOWNLOAD_DIR, file_name)
            with open(file_path, "wb") as f:
                bytes_received = 0
                while bytes_received < file_size:
                    chunk = client.recv(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_received += len(chunk)
                    print(f"[PROGRESS] {bytes_received}/{file_size} bytes received.", end="\r")
            print(f"\n[COMPLETE] {file_name} downloaded successfully.")
        except ConnectionRefusedError:
            raise ConnectionRefusedError("[ERROR] Could not connect to the server.")

def main():
    print("[CLIENT] Starting...")
    already_downloaded = set()

    while True:
        if not os.path.exists(INPUT_FILE):
            print(f"[WARNING] {INPUT_FILE} not found.")
            time.sleep(5)
            continue

        try:
            with open(INPUT_FILE, "r") as f:
                files_to_download = {line.strip() for line in f if line.strip()}

            new_files = files_to_download - already_downloaded
            for file_name in new_files:
                download_file(file_name)
                already_downloaded.add(file_name)

        except ConnectionRefusedError as e:
            print(e)
            print("[CLIENT] Closing program in 3 seconds...")
            time.sleep(3)
            sys.exit()

        print("[INFO] Waiting for new files...")
        time.sleep(5)

if __name__ == "__main__":
    main()
