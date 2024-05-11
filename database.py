import sqlite3
import config
import math
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)

def create_table(db_name="messages.db"):
    try:
        logging.info("Создание БД")
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                message TEXT,
                tts_symbols INTEGER,
                stt INTEGER)
            ''')
            conn.commit()
    except Exception as e:(
        print(f"Error: {e}"))

def insert_row(user_id, message, tts_symbols, db_name="messages.db"):
    try:
        logging.info("Добавление tts")
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO messages (user_id, message, tts_symbols)VALUES (?, ?, ?)''',
                           (user_id, message, tts_symbols))
            conn.commit()
    except Exception as e:
        print(f"Error: {e}")

def insert_row2(user_id, message, cell, value, db_name="messages.db"):
    try:
        logging.info("Добавление stt")
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''INSERT INTO messages (user_id, message, {cell}) VALUES (?, ?, ?)''',
                           (user_id, message, value))
            conn.commit()
    except Exception as e:
        print(f"Error: {e}")

def insert_row3(user_id, message, db_name="messages.db"):
    try:
        logging.info("Добавление ответа нейросети")
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''INSERT INTO messages (user_id, message) VALUES (?, ?)''',
                           (user_id, message))
            conn.commit()
    except Exception as e:
        print(f"Error: {e}")

def count_all_symbol(user_id, db_name="messages.db"):
    try:
        logging.info("Подсчет tts")
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT SUM(tts_symbols) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            if data and data[0]:
                return data[0]
            else:
                return 0
    except Exception as e:
        print(f"Error: {e}")

def count_all_blocks(user_id, db_name="messages.db"):
    try:
        logging.info("Подсчет stt")
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT SUM(stt) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            if data and data[0]:
                return data[0]
            else:
                return 0
    except Exception as e:
        print(f"Error: {e}")

def is_tts_symbol_limit(message, text):
    logging.info("Проверка лимита tts")
    user_id = message.from_user.id
    text_symbols = len(text)
    all_symbols = count_all_symbol(user_id) + text_symbols
    if all_symbols >= config.MAX_USER_TTS_SYMBOLS:
        msg = f"Превышен общий лимит SpeechKit TTS {config.MAX_USER_TTS_SYMBOLS}. Использовано: {all_symbols} символов. Доступно: {config.MAX_USER_TTS_SYMBOLS - all_symbols}"
        return msg
    if text_symbols >= config.MAX_TTS_SYMBOLS:
        msg = f"Превышен лимит SpeechKit TTS на запрос {config.MAX_TTS_SYMBOLS}, в сообщении {text_symbols} символов"
        return msg
    return all_symbols

def is_stt_block_limit(message, duration):
    logging.info("Проверка лимита stt")
    user_id = message.from_user.id
    audio_blocks = math.ceil(duration / 15)
    all_blocks = count_all_blocks(user_id) + audio_blocks

    if duration >= 30:
        msg = "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"
        return msg

    if all_blocks >= config.MAX_USER_STT_SYMBOLS:
        msg = f"Превышен общий лимит SpeechKit STT {config.MAX_USER_STT_SYMBOLS}. Использовано {all_blocks} блоков. Доступно: {config.MAX_USER_STT_SYMBOLS - all_blocks}"
        return msg

    return audio_blocks