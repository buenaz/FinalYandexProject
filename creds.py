import json
import logging
import time
from datetime import datetime
import requests
import config

logging.basicConfig(filename='log_file.txt', level=logging.INFO,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")

# получение нового iam_token
def create_new_token():
    url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {
        "Metadata-Flavor": "Google"
    }
    try:
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            token_data['expires_at'] = time.time() + token_data['expires_in']
            iam_token = config.iam_token
            with open(iam_token, "w") as token_file:
                json.dump(token_data, token_file)
            logging.info("Получен новый iam_token")
        else:
            logging.error(f"Ошибка получения iam_token. Статус-код: {response.status_code}")
    except Exception as e:
        logging.error(f"Ошибка получения iam_token: {e}")

def get_creds():
    try:
        iam_token = config.iam_token
        print(iam_token)
        with open(iam_token, 'r') as f:
            file_data = json.load(f)
            expiration = datetime.strptime(file_data["expires_at"][:26], "%Y-%m-%dT%H:%M:%S.%f")
        if expiration < datetime.now():
            logging.info("Срок годности iam_token истёк")
            create_new_token()
    except:
        create_new_token()

    with open(iam_token, 'r') as f:
        file_data = json.load(f)
        print(file_data)
        iam_token = file_data["access_token"]

    folder_id = config.folder_id
    with open(folder_id, 'r') as f:
        folder_id = f.read().strip()
        print(file_data)

    return iam_token, folder_id

def get_bot_token():
    bot_token = config.bot_token
    with open(bot_token, 'r') as f:
        return f.read().strip()
