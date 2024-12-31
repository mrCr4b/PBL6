from mitmproxy import http
from datetime import datetime
import os
import re

# Đường dẫn tới file log và danh sách các URL cho phép
temp_file_path = "D:\\Documents\\Study\\pbl6\\code\\temp.txt"
log_file_path = "D:\\Documents\\Study\\pbl6\\code\\logs.txt"
list_file_path = "D:\\Documents\\Study\\pbl6\\code\\list.txt"

# Tải danh sách URL bị chặn vào bộ nhớ
def load_blocked_urls():
    with open(list_file_path, "r") as file:
        blocked_urls = [line.strip() for line in file if line.strip()]
    return blocked_urls

# Biến toàn cục
blocked_urls = load_blocked_urls()
list_file_mtime = os.stat(list_file_path).st_mtime  # Lưu dấu thời gian chỉnh sửa của file

def check_file_update():
    global blocked_urls, list_file_mtime
    current_mtime = os.stat(list_file_path).st_mtime
    if current_mtime != list_file_mtime:  # Nếu file bị chỉnh sửa
        list_file_mtime = current_mtime
        blocked_urls = load_blocked_urls()  # Nạp lại danh sách URL
        print(f"Reloaded blocked URLs: {blocked_urls}")  # Debug thông báo nạp lại danh sách

def request(flow: http.HTTPFlow) -> None:
    # Kiểm tra nếu file `list.txt` đã thay đổi
    check_file_update()
    
    # Kiểm tra nếu URL trong request KHÔNG khớp với bất kỳ URL nào trong danh sách cho phép
    if not any(url in flow.request.pretty_url for url in blocked_urls) and "git-receive-pack" in flow.request.pretty_url:
        # Lấy thời gian request
        request_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        
        # Lấy địa chỉ IP của client
        client_ip = flow.client_conn.address[0]
        
        # Rút gọn URL để chỉ giữ lại phần sau "github.com/"
        full_url = flow.request.pretty_url
        match = re.search(r"github\.com/([^/]+/[^/]+)", full_url)
        if match:
            short_url = match.group(1)  # Lấy phần rút gọn của URL
        else:
            short_url = "Unknown URL"  # Nếu không khớp mẫu, trả về giá trị mặc định

        # Tạo log message với định dạng yêu cầu
        temp_message = f"{request_time}\n{short_url}\n{client_ip}"
        log_message = f"{request_time}\n{short_url}\n{client_ip}\n\n"

        # Ghi log vào file khi có request bị chặn
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(temp_message)

        with open(log_file_path, "a") as log_file:
            log_file.write(log_message)

        # Trả về HTTP 403 Forbidden
        flow.response = http.Response.make(
            403,  # Mã trạng thái HTTP
            b"Ban khong duoc phep git push toi repo nay.",  # Nội dung phản hồi
            {"Content-Type": "text/plain"}  # Headers
        )
