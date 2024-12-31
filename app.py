from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
import threading
import subprocess

app = Flask(__name__)
socketio = SocketIO(app)

# Đường dẫn đến file log
log_file_path = "D:\\Documents\\Study\\pbl6\\code\\temp.txt"
log_file_path_mail = "D:\\Documents\\Study\\pbl6\\code\\temp_mail.txt"
list_file_path = "D:\\Documents\\Study\\pbl6\\code\\list.txt"
mail_list_file_path = "D:\\Documents\\Study\\pbl6\\code\\mail_list.txt"

def read_list_file():
    with open(list_file_path, "r") as file:
        content = file.read()
    return content

def read_mail_list_file():
    with open(mail_list_file_path, "r") as file:
        content = file.read()
    return content


# Hàm đọc nội dung từ file log
def read_log():
    logs = []
    try:
        with open(log_file_path, 'r') as log_file:
            lines = log_file.readlines()
            # Đọc file theo nhóm 3 dòng
            for i in range(0, len(lines), 3):
                log_entry = {
                    'time': lines[i].strip(),  # Dòng 1: thời gian
                    'repo': lines[i + 1].strip(),  # Dòng 2: repo
                    'ip': lines[i + 2].strip()  # Dòng 3: IP
                }
                logs.append(log_entry)
    except FileNotFoundError:
        logs = [{"time": "N/A", "repo": "N/A", "ip": "N/A"}]  # Trường hợp file không tồn tại
    return logs

# Hàm đọc nội dung từ file log mail
def read_log_2():
    logs = []
    try:
        with open(log_file_path_mail, 'r') as log_file:
            lines = log_file.readlines()
            # Đọc file theo nhóm 3 dòng
            for i in range(0, len(lines), 3):
                log_entry = {
                    'time': lines[i].strip(),  # Dòng 1: thời gian
                    'from': lines[i + 1].strip(),  # Dòng 2: repo
                    'to': lines[i + 2].strip()  # Dòng 3: IP
                }
                logs.append(log_entry)
    except FileNotFoundError:
        logs = [{"time": "N/A", "from": "N/A", "to": "N/A"}]  # Trường hợp file không tồn tại
    return logs

def send_message_in_thread():
    subprocess.run(['python', 'D:\\Documents\\Study\\pbl6\\code\\send_messages.py'])

def send_message_in_thread_2():
    subprocess.run(['python', 'D:\\Documents\\Study\\pbl6\\code\\send_messages_mail.py'])

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, debounce_interval=1.0):
        super().__init__()
        self.debounce_interval = debounce_interval
        self.last_event_time = 0
        self.last_event_time_2 = 0

    def on_modified(self, event):
        # Chỉ xử lý nếu file bị sửa đổi và là file log đã chỉ định
        if event.src_path == log_file_path:
            current_time = time.time()
            # Kiểm tra khoảng thời gian từ lần sửa đổi gần nhất
            if current_time - self.last_event_time > self.debounce_interval:
                logs = read_log()
                socketio.emit('update_logs', logs)  # Gửi dữ liệu logs tới tất cả client qua WebSocket
                print("Log updated and emitted.")
                self.last_event_time = current_time
                # Gửi tin nhắn telegram
                threading.Thread(target=send_message_in_thread).start()
                # Chỉ xử lý nếu file bị sửa đổi và là file log đã chỉ định
        if event.src_path == log_file_path_mail:
            current_time_2 = time.time()
            # Kiểm tra khoảng thời gian từ lần sửa đổi gần nhất
            if current_time_2 - self.last_event_time_2 > self.debounce_interval:
                logs = read_log_2()
                socketio.emit('update_mail_logs', logs)  # Gửi dữ liệu logs tới tất cả client qua WebSocket
                print("Log updated and emitted.")
                self.last_event_time_2 = current_time_2
                # Gửi tin nhắn telegram
                threading.Thread(target=send_message_in_thread_2).start()

# Đăng ký đường dẫn cho file HTML
@app.route('/')
def index():
    file_content = read_list_file()
    mail_file_content = read_mail_list_file()
    return render_template("index.html", file_content=file_content, mail_file_content=mail_file_content)

# Khởi động watchdog để giám sát file log
def start_watchdog():
    event_handler = LogFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(log_file_path), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)  # Duy trì vòng lặp để watchdog hoạt động
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

@app.route('/save-list', methods=['POST'])
def save_list():
    data = request.get_json()
    if 'content' in data:
        try:
            with open(list_file_path, "w") as file:
                file.write(data['content'])
            return jsonify({"message": "Success"}), 200
        except Exception as e:
            print(f"Error saving file: {e}")
            return jsonify({"message": "Error"}), 500
    return jsonify({"message": "Invalid data"}), 400

@app.route('/save-mail-list', methods=['POST'])
def save_mail_list():
    data = request.get_json()
    if 'content' in data:
        try:
            with open(mail_list_file_path, "w") as file:
                file.write(data['content'])
            return jsonify({"message": "Success"}), 200
        except Exception as e:
            print(f"Error saving file: {e}")
            return jsonify({"message": "Error"}), 500
    return jsonify({"message": "Invalid data"}), 400

# Ham chay mitmproxy
def run_mitmproxy():
    # Chạy mitmdump với script độc lập
    os.system('mitmdump -s "D:\\Documents\\Study\\pbl6\\code\\mitm_proxy_script.py" --listen-port 8899 > mitmproxy_output.log 2>&1')

# Ham chay mail
mail_server_process = None

def run_mail_server():
    """Chạy mail_server.py trong một subprocess."""
    global mail_server_process
    mail_server_process = subprocess.Popen(
        ['python', 'D:\\Documents\\Study\\pbl6\\code\\mail_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("Mail server started.")

def stop_mail_server():
    """Dừng mail_server.py nếu đang chạy."""
    global mail_server_process
    if mail_server_process:
        mail_server_process.terminate()
        mail_server_process.wait()
        print("Mail server stopped.")

if __name__ == '__main__':
    # Tạo thread để chạy mitmproxy
    t = threading.Thread(target=run_mitmproxy)
    t.daemon = True
    t.start()

    # Chạy mail_server.py trong luồng riêng
    mail_server_thread = threading.Thread(target=run_mail_server)
    mail_server_thread.daemon = True
    mail_server_thread.start()

    # Chạy watchdog trong luồng riêng
    threading.Thread(target=start_watchdog, daemon=True).start()
    
    try:
        socketio.run(app, debug=True)
    finally:
        # Đảm bảo tiến trình mail_server được dừng khi Flask thoát
        stop_mail_server()
