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
    filtered_files = [file for file in files if file not in ["server.py", "list.txt"]]
    
    with open(os.path.join(BASE_DIR, "list.txt"), "w") as f:
        for file in filtered_files:
            f.write(file + "\n")
    
    return filtered_files

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
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    server.settimeout(TIMEOUT)
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    try:
        while True:
            try:
                request_packet, client_addr = server.recvfrom(BUFFER_SIZE)
                request = request_packet.decode(FORMAT).strip()

                if request == "LIST":
                    files = update_file_list()
                    files_str = "\n".join(files)
                    server.sendto(files_str.encode(FORMAT), client_addr)
                    print(f"[LIST] Sent file list to {client_addr}")
                else:
                    file_name = request.replace("REQUEST:", "").strip()

                    if not file_name:
                        print(f"[ERROR] Invalid file request from {client_addr}.")
                        continue

                    print(f"[REQUEST] Client {client_addr} requested file: {file_name}")
                    send_file(server, client_addr, file_name)

            except socket.timeout:
                continue  # Continue listening for new requests
            except KeyboardInterrupt:
                print("\n[SERVER] Shutting down...")
                break

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

    finally:
        server.close()
        print("[SERVER] Server has been shut down.")

if __name__ == "__main__":
    main()