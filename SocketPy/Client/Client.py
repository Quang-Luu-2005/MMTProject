import socket
import threading
import os
import time

FORMAT = "utf-8"
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
process_display = {}

display_process_lock = threading.Lock()

def display_process(num_parts):
    os.system('cls' if os.name == 'nt' else 'clear')

    for file_name in process_display:

        print(f"-------| {file_name} |-------")

        if len(process_display[file_name]) == 1:
            print("Download completely")  
        else:  
            for i in range(num_parts):
                print(f"Part {i + 1} . . . {process_display[file_name][i]}%")

        for i in range(len(file_name) + 18):
            print("=", end = "")
        print(" ")


def download_chunk(file_name, offset, chunk_size, server_ip, server_port, part):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((server_ip, server_port))
            request = f"DOWNLOAD {file_name} {offset} {chunk_size}"
            client.send(request.encode(FORMAT))

            file_part_path = os.path.join(DOWNLOAD_FOLDER, f"{file_name}.part{part}")
            with open(file_part_path, "wb") as f:
                total_len = 0
                while total_len < chunk_size:
                    data = client.recv(1024)
                    if not data:
                        continue
                    total_len += len(data)
                    f.write(data)

                    process = total_len / chunk_size * 100
                    process_display[file_name][part - 1] = round(process, 2)

                    # luồng hiện tại chỉ đựoc gọi display_process khi tiến độ nó của tăng tới ngưỡng bội số nguyên của 3
                    if process % 2 == 0:
                        with display_process_lock:
                            display_process(4)
            
            process_display[file_name][part - 1] = 100
            client.close()

def merge_files(filename, num_parts):
    # Ghép các file con thành file hoàn chỉnh
    with open(os.path.join(DOWNLOAD_FOLDER, filename), "wb") as f_out:
        for i in range(num_parts):
            part_file_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.part{i + 1}")
            with open(part_file_path, "rb") as f_in:
                f_out.write(f_in.read())
            os.remove(part_file_path)  # Xóa file con sau khi hoàn tất gép file
    print(f"Merged {filename} completely.")

def download_file(file_name, file_size, server_ip, server_port):
    threads = []
    chunk_size = file_size // 4

    for i in range(4):
        offset = i * chunk_size
        chunk_len = 0 
        if i < 3:
            chunk_len = chunk_size
        else:
            chunk_len = file_size - offset
        thread = threading.Thread(target=download_chunk, args=(file_name, offset, chunk_len, server_ip, server_port, i + 1))
        threads.append(thread)
        thread.start()

    # đợi các thread trong threads hoàn thành rồi mới tiếp
    for thread in threads:
        thread.join()

    merge_files(file_name, 4)
    process_display[file_name] = ["Download completely"]
    # del process_display[file_name]

def main():
    server_ip = "127.0.0.1"
    server_port = 65432

    data = None
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((server_ip, server_port))
        client.send("LIST".encode(FORMAT))
        data = client.recv(4096).decode(FORMAT)

    files = dict(line.split() for line in data.splitlines())
    downloaded_files = set()

    while True:
        print("Available files:")
        print(data)
        print("Please run file getInput.py to enter files you'd like to download.")
        print("Press Ctrl + C to exit")

        input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input.txt")
        if os.path.exists(input_file):
            flag = 0

            with open(input_file, "r") as f:
                files_to_download = [line.strip() for line in f if line.strip() not in downloaded_files]

            for file_name in files_to_download:
                if file_name == None or file_name == "":
                    continue

                process_display[file_name] = [0] * 4

                if file_name in files:
                    file_size = int(files[file_name])
                    print(f"Downloading {file_name}...")
                    download_file(file_name, file_size, server_ip, server_port)
                    downloaded_files.add(file_name)
                else:
                    print(f"File {file_name} not found on server.")

                    # xóa file không tồn tại đó ra khỏi file input.txt
                    files_to_download.remove(file_name)
                    flag = 1

                if flag == 1:
                    # xóa file không tồn tại đó ra khỏi file input.txt
                    with open(input_file, "r") as f:  
                        lines = f.readlines()   

                    lines = [line.strip() for line in lines]

                    lines.remove(file_name)

                    with open(input_file, "w") as f:  
                        f.write('\n'.join(lines) + '\n')   


        time.sleep(5)
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    try:
        main()
    except KeyboardInterrupt:
        print("Client out")
        exit()
