import requests

bot_token = '7634550186:AAEqRV42QXNnlCgJsIEhXVv4JWZYP54MMek'
url = f'https://api.telegram.org/bot{bot_token}/getUpdates'
response = requests.get(url)
updates = response.json()

print(updates)
