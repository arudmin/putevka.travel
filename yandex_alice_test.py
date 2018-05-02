# -*- coding: utf-8 -*-

import os, json
import telebot
import redis
from telebot import types
from flask import Flask, jsonify, abort, redirect, url_for
from flask import session, escape, request
from googletrans import Translator

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

translator = Translator()

# bot = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])
# bot_name = bot.get_me().username
redis = redis.from_url(os.environ['REDIS_URL'], charset='utf-8', decode_responses=True)


response = json.loads('''
{
  "response": {
    "text": "",
    "tts": "",
    "buttons": [
        {
            "title": "test button",
            "payload": {},
            "url": "https://example.com/",
            "hide": true
        }
    ],
    "end_session": false
  },
  "session": {
    "session_id": "",
    "message_id": 0,
    "user_id": ""
  },
  "version": "1.0"
}''')


@app.route("/alice", methods=['POST'])
@app.route("/alice/", methods=['POST'])
def search():
    post_data = request.json

# meta - Информация об устройстве, с помощью которого пользователь разговаривает с Алисой.

    # locale - Язык в POSIX-формате, максимум 64 байта.
    locale = post_data['meta']['locale']

    # timezone - Название часового пояса, включая алиасы, максимум 64 байта.
    timezone = post_data['meta']['timezone']

    # client_id - Идентификатор устройства и приложения, в котором идет разговор, максимум 1024 байта.
    client_id = post_data['meta']['client_id']

# request - Данные, полученные от пользователя.

    # type - Тип ввода, обязательное свойство. Возможные значения:
    #     "SimpleUtterance" — голосовой ввод;
    #     "ButtonPressed" — нажатие кнопки.
    request_type = post_data['request']['type']

    # markup - Формальные характеристики реплики, которые удалось выделить Яндекс.Диалогам. Отсутствует, если ни одно из вложенных свойств не применимо.
    # dangerous_context = post_data['request']['markup']['dangerous_context']

    # command - Текст пользовательского запроса без активационных фраз Алисы и конкретного навыка, максимум 1024 байта. Может быть пустым.
    command = post_data['request']['command']

    # original_utterance - Полный текст пользовательского запроса, максимум 1024 байта.
    original_utterance = post_data['request']['original_utterance']

    # payload - JSON, полученный с нажатой кнопкой от обработчика навыка (в ответе на предыдущий запрос), максимум 4096 байт
    # payload = post_data['request']['payload']

# session - Данные о сессии.
    # new	- Признак новой сессии. Возможные значения:
    #     true — пользователь начал новый разговор с навыком;
    #     false — запрос отправлен в рамках уже начатого разговора.
    session_is_new = post_data['session']['new']

    # session_id - Уникальный идентификатор сессии, максимум 64 байта.
    session_id = post_data['session']['session_id']
    message_id = post_data['session']['message_id']
    skill_id = post_data['session']['skill_id']
    user_id = post_data['session']['user_id']

    response['session']['session_id'] = session_id
    response['session']['message_id'] = message_id
    response['session']['user_id'] = user_id

    response['response']['text'] = get_response(command)

    return jsonify(response)


def get_response(request):
    return 'Вы сказали ' + request

# if __name__ == '__main__':
    # bot.polling(none_stop=True)


# Default port:
if __name__ == '__main__':
    # app.run()
    app.run(debug=True)
