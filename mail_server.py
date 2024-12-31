from aiosmtpd.controller import Controller
from email.message import EmailMessage
from email import message_from_string
import os
import smtplib
from datetime import datetime

mail_list_file_path = "D:\\Documents\\Study\\pbl6\\code\\mail_list.txt"
log_file_path = "D:\\Documents\\Study\\pbl6\\code\\logs_mail.txt"
temp_file_path = "D:\\Documents\\Study\\pbl6\\code\\temp_mail.txt"

class RelayHandler:
    def __init__(self, relay_host, relay_port, username=None, password=None):
        self.relay_host = relay_host
        self.relay_port = relay_port
        self.username = username
        self.password = password

        # Khởi tạo danh sách được phép và theo dõi thời gian cập nhật file
        self.allowed_list = []
        self.last_modified_time = 0
        self.load_allowed_list()

    def load_allowed_list(self):
        """Đọc danh sách email/tên miền được phép từ tệp."""
        try:
            current_mtime = os.path.getmtime(mail_list_file_path)
            if current_mtime != self.last_modified_time:
                # Tải lại danh sách nếu file được cập nhật
                with open(mail_list_file_path, "r") as file:
                    self.allowed_list = [line.strip() for line in file if line.strip()]
                self.last_modified_time = current_mtime
                print("Allowed list updated.")
        except FileNotFoundError:
            print(f"File {mail_list_file_path} không tồn tại!")
            self.allowed_list = []

    def log_blocked_email(self, mail_from, recipient):
        """Ghi thông tin email bị chặn vào file log và file temp."""
        timestamp = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        log_content = f"{timestamp}\n{mail_from}\n{recipient}\n\n"
        temp_content = f"{timestamp}\n{mail_from}\n{recipient}"

        # Ghi vào file log (nối tiếp)
        with open(log_file_path, "a") as log_file:
            log_file.write(log_content)

        # Ghi vào file temp (ghi đè)
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(temp_content)

    async def handle_DATA(self, server, session, envelope):
        # Tự động kiểm tra và cập nhật danh sách
        self.load_allowed_list()

        mail_from = envelope.mail_from
        rcpt_tos = envelope.rcpt_tos
        mail_data = envelope.content.decode('utf-8')

        # Phân tích cú pháp mail_data thành một email
        email_message = message_from_string(mail_data)
        # Lấy Subject
        subject = email_message['Subject']
        # Lấy phần nội dung (body) của email
        if email_message.is_multipart():
            for part in email_message.iter_parts():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8')
        else:
            body = email_message.get_payload(decode=True).decode('utf-8')

        # Kiểm tra email đích
        for recipient in rcpt_tos:
            domain = recipient.split("@")[-1]  # Tách tên miền từ email
            if recipient not in self.allowed_list and domain not in self.allowed_list:
                print(f"Blocked email to: {recipient}")
                self.log_blocked_email(mail_from, recipient)
                return "550 Email blocked by policy"

        # Gửi email qua relay SMTP server
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg["From"] = mail_from
            msg["To"] = ", ".join(rcpt_tos)
            msg["Subject"] = subject

            with smtplib.SMTP(self.relay_host, self.relay_port) as smtp:
                if self.username and self.password:
                    smtp.starttls()
                    smtp.login(self.username, self.password)
                smtp.send_message(msg)
                print("Email successfully relayed")
        except Exception as e:
            print(f"Failed to relay email: {e}")
            return f"451 {e}"

        return "250 Message accepted for delivery"


if __name__ == "__main__":
    # Cấu hình relay host (ví dụ: smtp.gmail.com)
    RELAY_HOST = "smtp.gmail.com"
    RELAY_PORT = 587
    USERNAME = "slowcrab2003@gmail.com"  # Đặt None nếu không cần xác thực
    PASSWORD = "wapc hdxv ogvz wigg"  # Đặt None nếu không cần xác thực

    # Khởi tạo handler và controller
    handler = RelayHandler(RELAY_HOST, RELAY_PORT, USERNAME, PASSWORD)
    #controller = Controller(handler, hostname="127.0.0.1", port=1025)
    controller = Controller(handler, hostname="192.168.1.14", port=1025)



    # Chạy SMTP relay server
    print("Starting SMTP relay server on port 1025...")
    try:
        controller.start()
        input("Press Enter to stop the server...\n")
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        controller.stop()
