import socket
import os
import struct

HOST = "127.0.0.1"  # Loopback IP address
PORT = 65432
BUFFER_SIZE = 1024
CHUNK_SIZE = 1015  # Adjusted to account for header size (9 bytes)
FORMAT = "utf-8"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Server directory
TIMEOUT = 2  # Retransmission timeout (in seconds)

# Update list.txt with files in the Server directory
def update_file_list():
    files = [f for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))]
    with open(os.path.join(BASE_DIR, "list.txt"), "w") as f:
        for file in files:
            if file not in ["server.py", "list.txt"]:
                f.write(file + "\n")

# Calculate a simple checksum for error detection
def checksum(data):
    return sum(data) % 256

# Send a file to the client
def send_file(server, client_addr, file_name):
    file_path = os.path.join(BASE_DIR, file_name)
    if not os.path.exists(file_path):
        error_message = "ERROR: File not found.\n".encode(FORMAT)
        server.sendto(error_message, client_addr)
        return

    file_size = os.path.getsize(file_path)
    # Notify client about file size
    size_message = f"OK:{file_size}\n".encode(FORMAT)
    server.sendto(size_message, client_addr)

    with open(file_path, "rb") as f:
        seq_num = 0
        total_bytes_sent = 0

        while total_bytes_sent < file_size:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break

            chunk_len = len(chunk)
            packet_checksum = checksum(chunk)
            # Include chunk length in the packet
            packet = struct.pack(f"I I B {CHUNK_SIZE}s", seq_num, chunk_len, packet_checksum, chunk.ljust(CHUNK_SIZE, b'\x00'))
            while True:
                server.sendto(packet, client_addr)
                try:
                    # Wait for ACK
                    ack_packet, _ = server.recvfrom(BUFFER_SIZE)
                    ack_seq_num, ack_status = struct.unpack("I B", ack_packet)

                    if ack_status == 0 and ack_seq_num == seq_num:  # ACK is correct
                        total_bytes_sent += chunk_len
                        break
                except socket.timeout:
                    print(f"[TIMEOUT] Resending packet {seq_num}...")
            seq_num += 1

    print(f"[SENT] {file_name} to client. ({total_bytes_sent}/{file_size} bytes sent)")

def main():
    update_file_list()
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    server.settimeout(TIMEOUT)
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    try:
        while True:
            try:
                request_packet, client_addr = server.recvfrom(BUFFER_SIZE)
                file_name = request_packet.decode(FORMAT).strip().replace("REQUEST:", "")

                if not file_name:
                    print(f"[ERROR] Invalid file request from {client_addr}.")
                    continue

                print(f"[REQUEST] Client {client_addr} requested file: {file_name}")
                send_file(server, client_addr, file_name)

            except socket.timeout:
                continue  # Continue listening for new requests
            except KeyboardInterrupt:
                break

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server shutting down.")
    finally:
        server.close()
        print("[CLOSED] Server has been closed.")

if __name__ == "__main__":
    main()
