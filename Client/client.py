import os
import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 65432
FORMAT = "utf-8"
DOWNLOAD_FOLDER = "downloads"
CHUNK_SIZE = 1024 * 1024  # 1MB per chunk (or adjust according to the actual chunk size)

def download_chunk(part_index, filename, offset, total_size):
    """ Tải một phần của file và hiển thị tiến độ từng phần """
    file_part_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.part{part_index}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        request = f"{filename} {offset}"
        client.send(request.encode(FORMAT))

        with open(file_part_path, "wb") as f:
            total_received = 0
            while True:
                data = client.recv(CHUNK_SIZE)
                if not data:
                    break
                f.write(data)
                total_received += len(data)

                # Cập nhật tiến độ phần này
                progress = (total_received / total_size) * 100
                print(f"Downloading {filename} part {part_index + 1} .... {progress:.2f}%")

def monitor_input_file():
    """ Kiểm tra file input.txt để lấy danh sách file cần tải """
    while True:
        with open("input.txt", "r") as f:
            files_to_download = f.read().splitlines()

        for filename in files_to_download:
            if not os.path.exists(os.path.join(DOWNLOAD_FOLDER, filename)):
                download_file(filename)
        
        time.sleep(5)  # Đọc lại file mỗi 5 giây

def download_file(filename):
    """ Tải toàn bộ file bằng cách chia thành 4 phần """
    total_size = 100 * 1024 * 1024  # Giả sử kích thước file là 100MB (thay đổi theo thực tế)
    threads = []
    
    # Chia file thành 4 phần
    for i in range(4):
        offset = i * (total_size // 4)
        thread = threading.Thread(target=download_chunk, args=(i, filename, offset, total_size))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Sau khi tải xong tất cả các phần, ghép lại các phần thành file hoàn chỉnh
    merge_parts(filename, 4)

def merge_parts(filename, num_parts):
    """ Ghép các phần đã tải lại thành một file hoàn chỉnh """
    with open(os.path.join(DOWNLOAD_FOLDER, filename), "wb") as f_out:
        for i in range(num_parts):
            part_file_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.part{i}")
            with open(part_file_path, "rb") as f_in:
                f_out.write(f_in.read())
            os.remove(part_file_path)  # Xóa phần sau khi ghép lại

if __name__ == "__main__":
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    try:
        monitor_input_file()
    except KeyboardInterrupt:
        print("Client stopped.")
