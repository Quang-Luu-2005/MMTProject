
import socket
import os
import time
import sys
import struct

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432
CHUNK_SIZE = 1024
FORMAT = "utf-8"
INPUT_FILE = os.path.join(os.path.dirname(__file__), "input.txt")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# Ensure the downloads directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

TIMEOUT = 2  # Timeout for retransmissions (in seconds)
MAX_RETRIES = 5  # Maximum number of retries per packet


def checksum(data):
    """Calculate a simple checksum for error detection."""
    return sum(data) % 256


def download_file(file_name):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.settimeout(TIMEOUT)
        try:
            # Send the file request
            request_packet = f"REQUEST:{file_name}".encode(FORMAT)
            client.sendto(request_packet, (SERVER_HOST, SERVER_PORT))

            # Receive server's response (file size or error)
            try:
                response, server_addr = client.recvfrom(CHUNK_SIZE)
                response = response.decode(FORMAT)

                if response.startswith("ERROR"):
                    print(f"[ERROR] {response}")
                    return

                _, file_size = response.split(":")
                file_size = int(file_size)
                print(f"[INFO] Downloading {file_name} ({file_size} bytes)...")

            except socket.timeout:
                print("[ERROR] No response from server.")
                return

            # Initialize file download
            file_path = os.path.join(DOWNLOAD_DIR, file_name)
            with open(file_path, "wb") as f:
                bytes_received = 0
                expected_seq = 0

                while bytes_received < file_size:
                    for _ in range(MAX_RETRIES):
                        try:
                            # Receive a packet
                            packet, server_addr = client.recvfrom(CHUNK_SIZE + 8)
                            seq_num, received_checksum, chunk = struct.unpack(
                                "I B 1024s", packet[:8] + packet[8:]
                            )
                            chunk = chunk.rstrip(b"\x00")

                            # Verify checksum and sequence number
                            if checksum(chunk) == received_checksum and seq_num == expected_seq:
                                f.write(chunk)
                                bytes_received += len(chunk)
                                print(f"[PROGRESS] {bytes_received}/{file_size} bytes received.", end="\r")

                                # Send ACK
                                ack_packet = struct.pack("I B", seq_num, 0)  # ACK = 0
                                client.sendto(ack_packet, server_addr)

                                # Move to the next sequence
                                expected_seq += 1
                                break
                            else:
                                print("[ERROR] Packet error. Resending ACK for last valid packet.")
                                ack_packet = struct.pack("I B", expected_seq - 1, 0)
                                client.sendto(ack_packet, server_addr)

                        except socket.timeout:
                            print("[WARNING] Timeout waiting for packet. Retrying...")
                            continue
                    else:
                        print("[ERROR] Max retries reached. Download failed.")
                        return

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
