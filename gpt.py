import requests
import config
import logging
from creds import get_creds

iam_token, folder_id = get_creds()
print(iam_token, folder_id)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)

def text_to_speech(text: str):
    iam_token = config.iam_token
    folder_id = config.folder_id

    headers = {
        'Authorization': f'Bearer {iam_token}',
    }
    data = {
        'text': text,
        'lang': 'ru-RU',
        'voice': 'filipp',
        'folderId': folder_id,
    }
    response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers, data=data)

    if response.status_code == 200:
        return True, response.content
    else:
        return False, "При запросе в SpeechKit возникла ошибка"
        logging.error("При запросе в SpeechKit возникла ошибка")


def speech_to_text(data):
    params = "&".join([
        "topic=general",
        f"folderId={config.folder_id}",
        "lang=ru-RU"
    ])

    headers = {
        'Authorization': f'Bearer {config.iam_token}',
    }

    response = requests.post(
        f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
        headers=headers,
        data=data
    )

    decoded_data = response.json()
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")
    else:
        return False, "При запросе в SpeechKit возникла ошибка"
        logging.error("При запросе в SpeechKit возникла ошибка")

def ask_gpt(collection, mode):
    if mode == 1:
        SYSTEM_PROMT = config.PROMPT1
    if mode == 2:
        SYSTEM_PROMT = config.PROMPT2
    if mode == 3:
        SYSTEM_PROMT = config.PROMPT3

    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {config.iam_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{config.folder_id}/yandexgpt",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 500
        },
        "messages": [
            {
                "role": "system",
                "text": SYSTEM_PROMT
            },
            {
                "role": "user",
                "text": collection
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        logging.info(response)
        return response.json()['result']['alternatives'][0]['message']['text']
    except Exception as e:
        result = "Произошла непредвиденная ошибка. Подробности см. в журнале."
        logging.error("Произошла непредвиденная ошибка.")