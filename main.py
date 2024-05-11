from database import create_table, insert_row, is_tts_symbol_limit, is_stt_block_limit, insert_row2, insert_row3
from gpt import text_to_speech, speech_to_text, ask_gpt
import telebot
import config
import logging
import schedule
from creds import get_bot_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)

bot = telebot.TeleBot(get_bot_token())
create_table()

@bot.message_handler(commands=['debug'])
def help(message):
    logging.info(f"Отправка отладочного сообщения пользователю {message.from_user.id}")
    bot.send_message(message.chat.id, 'Отладочная команда!')
    file_path = 'log_file.txt'
    with open(file_path, 'rb') as file:
        bot.send_document(message.chat.id, file)

def send_message_with_keyboard(chat_id, text, options):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
    for option in options:
        markup.add(telebot.types.KeyboardButton(option))
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.from_user.id, 'Привет! Я твой бот, со встроенным Yandex GPT и SpeechKit! Напиши текст или отправь голосовое и ты обязательно получишь ответ. Можешь использовать также команды /stt и /tts. Также можешь выбрать режим по команде /mode')
    logging.info("Отправка приветственного сообщения")

@bot.message_handler(commands=['mode'])
def modes(message):
    send_message_with_keyboard(message.from_user.id, "Ты можешь выбрать другой режим.", ['Обычный', 'Молодежный', 'Умный'])
    bot.register_next_step_handler(message, choose_mode)

def choose_mode(message):
    if message.text == 'Обычный':
        config.mode = 1
    if message.text == 'Молодежный':
        config.mode = 2
    if message.text == 'Умный':
        config.mode = 3
    return

@bot.message_handler(commands=['tts'])
def text(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь следующим сообщением текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, tts_for_block)

@bot.message_handler(commands=['stt'])
def text(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь следующим сообщением голосовое, чтобы я его распознал!')
    bot.register_next_step_handler(message, stt_for_block)

@bot.message_handler(content_types=['voice'])
def main_voice(message):
    logging.info("Получение голосового промта")
    stt(message)

@bot.message_handler(func=lambda message: True)
def main(message):
    user_id = message.from_user.id
    logging.info("Получение текстового промта")
    promt_text(message)

def promt(message, text):
    logging.info("Ответ Яндекс GPT для гс")
    m = config.mode
    response = ask_gpt(text, m)
    tts(message, response)


def promt_text(message):
    logging.info("Ответ Яндекс GPT для текста")
    m = config.mode
    response = ask_gpt(message.text, m)
    bot.send_message(message.chat.id, response)
    logging.info("Добавление в БД текста")
    insert_row3(message.from_user.id, response)

def tts_for_block(message):
    user_id = message.from_user.id
    text = message.text

    logging.info("/tts")
    if message.content_type != 'text':
        bot.send_message(user_id, 'Отправь текстовое сообщение')
        return

    text_symbol = is_tts_symbol_limit(message, text)

    insert_row(user_id, text, text_symbol)
    status, content = text_to_speech(text)

    if status:
        bot.send_voice(user_id, content)
    else:
        bot.send_message(user_id, content)

def tts(message, text):
    user_id = message.from_user.id
    logging.info("Перевод из ответа нейросети в гс")
    text_symbol = is_tts_symbol_limit(message, text)
    logging.info("Добавление в БД гс")
    insert_row(user_id, text, text_symbol)
    status, content = text_to_speech(text)

    if status:
        logging.info("Отправка гс от нейросети")
        bot.send_voice(user_id, content)
    else:
        logging.info("Ошибка в tts")
        bot.send_message(user_id, content)

def stt_for_block(message):
    user_id = message.from_user.id
    logging.info("/stt")
    if not message.voice:
        return

    stt_blocks = is_stt_block_limit(message, message.voice.duration)
    if not stt_blocks:
        return

    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)

    status, text = speech_to_text(file)

    if status:
        insert_row2(user_id, text, 'stt', stt_blocks)
        bot.send_message(user_id, text, reply_to_message_id=message.id)
    else:
        bot.send_message(user_id, text)

def stt(message):
    user_id = message.from_user.id
    logging.info("Расшифровка голосового промта")
    stt_blocks = is_stt_block_limit(message, message.voice.duration)
    if not stt_blocks:
        return

    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)

    status, text = speech_to_text(file)

    if status:
        insert_row2(user_id, text, 'stt', stt_blocks)
        logging.info("Добавление расшифровки в БД и отправка расшифрованного текста в промт")
        promt(message, text)
    else:
        logging.info("Ошибка в stt")
        promt(message, text)

bot.polling()