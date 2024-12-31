import asyncio
from telegram import Bot

bot_token = "7634550186:AAEqRV42QXNnlCgJsIEhXVv4JWZYP54MMek"
chat_id = "5996468166"
bot = Bot(token=bot_token)

log_file_path = "D:\\Documents\\Study\\pbl6\\code\\temp_mail.txt"

# Hàm đọc log
def read_log():
    logs = []
    try:
        with open(log_file_path, 'r') as log_file:
            lines = log_file.readlines()
            for i in range(0, len(lines), 3):
                log_entry = {
                    'time': lines[i].strip(),
                    'from': lines[i + 1].strip(),
                    'to': lines[i + 2].strip()
                }
                logs.append(log_entry)
    except FileNotFoundError:
        logs = [{"time": "N/A", "from": "N/A", "to": "N/A"}]
    return logs

# Coroutine gửi tin nhắn
async def send_latest_log():
    logs = read_log()
    if logs:
        latest_log = logs[-1]
        message = f"Đã phát hiện hành vi gửi e-mail bất thường:\nThời gian: {latest_log['time']}\nMail nguồn: {latest_log['from']}\nMail đích: {latest_log['to']}"
        await bot.send_message(chat_id=chat_id, text=message)
    else:
        print("No logs available to send.")

if __name__ == "__main__":
    asyncio.run(send_latest_log())
