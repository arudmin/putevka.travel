# -*- coding: utf-8 -*-
import telebot
import redis
import os, requests, time
import logging
from bs4 import BeautifulSoup as bs
# from apscheduler.schedulers.blocking import Bl    ockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from telebot import types
from telegraphapi import Telegraph  # https://github.com/MonsterDeveloper/python-telegraphapi
# <a>, <blockquote>, <br>, <em>, <figure>, <h3>, <h4>, <img>, <p>, <strong>
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

# scheduler = BlockingScheduler()
scheduler = BackgroundScheduler(daemon=False)

logging.basicConfig()
logging.getLogger("redis.connection").setLevel(logging.ERROR)
logging.getLogger("redis").setLevel(logging.ERROR)

telegraph = Telegraph()

redis = redis.from_url(os.environ['REDIS_URL'], charset='utf-8', decode_responses=True)
bot = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])

url = 'http://putevka.travel/'
bot_name = bot.get_me().username
channel_name = 'PutevkaTravel_new'
hideBoard = types.ReplyKeyboardRemove()


@bot.message_handler(commands=["start"])
def cmd_start(message):
    # check if command '/start' contains parameters and handle it
    request = message.text.replace('/start', '').strip()
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    requests_list = redis.smembers('items')

    if request.isdigit() and request in requests_list:
        redis.set('user:%s:name' % user_id, user_name)
        redis.set('user:%s:request' % user_id, request)
        redis.rpush('requests', {'user_id': user_id, 'request': request, 'timestamp': time.time()})
        welcome_msg = 'Здравствуйте, %s.\n\nВас заинтересовало сказочное предложение:\n*%s*\n\nХотите подобрать отель и уточнить детали поездки?' % (user_name, get_tour_name(request))
        kb_yesno = {'yes': 'Да', 'no': 'Нет'}
        keyboard = pages_inline_keyboard(kb_yesno)
        bot.send_message(message.chat.id, text=welcome_msg, parse_mode='Markdown', reply_markup=keyboard)
    else:
        msg = 'Пожалуйста, выберите направление для путешествия на отдельной странице @%s\n\nhttps://t.me/%s' % (channel_name, channel_name)
        bot.send_message(chat_id=message.chat.id, text=msg, reply_markup=hideBoard)

        # keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        # button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
        # button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
        # keyboard.add(button_phone)
        # bot.send_message(message.chat.id, text=request, reply_markup=keyboard)
        # reply = bot.send_message(message.chat.id, request, reply_markup=keyboard)
    # bot.register_next_step_handler(reply, after_start)
    return 0


@bot.callback_query_handler(func=lambda call: hasattr(call, 'data') and call.data in ['yes', 'no'])
def yes_no(message):
    answer = message.data
    user_id = message.from_user.id
    message = message.message
    request = redis.get('user:%s:request' % user_id)

    if answer == 'yes':
        msg = 'Вы выбрали направление:\n*%s*' % get_tour_name(request)
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', text=msg)

        msg = 'Пожалуйста, пришлите свой номер телефона, чтобы менеджер оперативно связался с вами и отправил в долгожданное путешествие.'
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        keyboard.add(types.KeyboardButton(text="Отправить номер телефона", request_contact=True))
        bot.send_message(chat_id=message.chat.id, text=msg, parse_mode='Markdown', reply_markup=keyboard)
    else:
        msg = 'Вероятно, произошла ошибка при выборе тура.'
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=msg)

        msg = 'Пожалуйста, выберите направление для путешествия на странице @%s\n\nhttps://t.me/%s' % (channel_name, channel_name)
        bot.send_message(chat_id=message.chat.id, text=msg)


@bot.message_handler(content_types=["contact"])
def read_contact_data(message):
    # print(message)
    user_id = message.from_user.id
    user_phone = message.contact.phone_number
    request = redis.get('user:%s:request' % user_id)

    if user_id == message.contact.user_id:
        redis.set('user:%s:phone' % user_id, user_phone)
        msg = 'Вы восхитительны!\n\nЗаявка принята и в ближайшее время менеджер позвонит по номеру %s, чтобы уточнить все детали путешествия.\n\nЖелаем Вам прекрасного дня!' % user_phone
        bot.send_message(chat_id=message.chat.id, text=msg, reply_markup=hideBoard)
    else:
        msg = 'Данный номер не пренадлежит вам. Сожалеем, но из-за мошенников, мы можем позвонить только владельцу этого аккаунта в телеграме. Пожалуйста, пришлите свой номер через кнопку внизу экрана.\n\nЕсли вы хотите, чтобы мы позвонили кому-то еще по поводу данной путевки, пожалуйста, отправьте эту ссылку владельцу номера телефона %s, чтобы он лично оставил заявку. Спасибо.' % user_phone
        bot.send_message(message.chat.id, msg)

        # msg = '[%s](https://t.me/%s?&start=%s)\n\nРаспродажа туров: https://t.me/PutevkaTravel_new' % (get_tour_name(request), bot_name, request)
        # msg = '[%s](https://t.me/%s?&start=%s)\n\n Распродажа туров: [https://t.me/PutevkaTravel_news](https://t.me/PutevkaTravel_new)' % (get_tour_name(request), bot_name, request)
        msg = '[%s](https://t.me/%s?&start=%s)' % (get_tour_name(request), bot_name, request)

        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        keyboard.add(types.KeyboardButton(text="Отправить номер телефона", request_contact=True))

        bot.send_message(chat_id=message.chat.id, text=msg, parse_mode='Markdown', reply_markup=keyboard)


# @scheduler.scheduled_job('interval', minutes=1)
def check_new_item(channel_name='@' + channel_name):
    r = requests.get(url)
    soup = bs(r.content, 'html.parser')
    items = soup.select('div.post')[1:]
    # redis.spop('items')
    try:
        saved_items = redis.smembers('items')  # get ids from redis DB
    except:
        saved_items = []

    pipe = redis.pipeline()

    for i in items:
        item = {}
        item['id'] = i.get('id').split('-')[1]

        if item['id'] in saved_items:
            continue
        print('add', item['id'])

        escape = lambda x: x.replace('`', '\'').replace('*', '✮')
        escape_tags = lambda x: x.replace('—', '\_').replace('.', '')

        _title = lambda x: _name(x)[0] + ', ' + _name(x)[1] + ' вместо ' + _name(x)[2]
        item['name'] = _title(i.h1.text)

        item['link'] = i.h1.a['href']
        item['image_url'] = i.img['src']
        item['conditions'] = i.find('div', 'entry').find_all('p').pop().text
        item['tags'] = [escape_tags(x.text.replace(' ', '')) for x in i.find('div', 'tags').find_all('a')]

        item['hotels'] = []
        _hotel = lambda x: _name(x)[0] + ', ' + _name(x)[1] + ' (' + stripe(_name(x)[2]) + ')'
        for x in i.find('div', 'entry').find_all('p')[1:-1]:
            try:
                item['hotels'] += [_hotel(x.text)]
            except:
                item['hotels'] += [x.text]

        # add item params to Redis DB
        pipe.sadd('items', item['id'])
        redis_db_name = 'item:%s' % item['id']
        for k, v in item.items():
            # print("-" * 10)
            if isinstance(v, (list, tuple)):
                if not v:
                    v = ['null']
                pipe.delete("%s:%s" % (redis_db_name, k))
                pipe.rpush("%s:%s" % (redis_db_name, k), *v)
            else:
                pipe.set("%s:%s" % (redis_db_name, k), v)

        # Composing Telegram Message
        msg = '[ ](%s)\n[%s](%s)\n\n' % (item['image_url'], item['name'], make_page(item))
        msg += "".join(['• {}\n'.format(x) for x in item['hotels']])
        msg += "\n%s\n\n" % item['conditions']
        msg += ", ".join(["#%s" % x for x in item['tags']])

        offer_link = "https://t.me/%s?&start=%s" % (bot_name, item['id'])
        kb_info = {
            offer_link: 'Оставить заявку',
            item['link']: 'Посмотреть на сайте',
        }
        keyboard = pages_inline_keyboard(kb_info, True)
        print(msg)
        bot.send_message(channel_name, text=msg, parse_mode='Markdown', reply_markup=keyboard)
        pipe.execute()
    bot.polling(none_stop=True)
    print('done')
    # return 0


def get_tour_name(tour_id):
    return redis.get('item:%s:name' % tour_id)


def pages_inline_keyboard(m, rows=False):
    keyboard = types.InlineKeyboardMarkup()
    btns = []
    if rows:
        for k, v in m.items():
            if is_url(k):
                keyboard.row(types.InlineKeyboardButton(text=v, url=k))
            else:
                keyboard.row(types.InlineKeyboardButton(text=v, callback_data=k))
    else:
        for k, v in m.items():
            if is_url(k):
                btns.append(types.InlineKeyboardButton(text=v, url=k))
            else:
                btns.append(types.InlineKeyboardButton(text=v, callback_data=k))
        keyboard.add(*btns)
    return keyboard  # возвращаем объект клавиатуры


def pages_reply_keyboard(m, rk=True, ot=False):
    kb_start = types.ReplyKeyboardMarkup(resize_keyboard=rk, one_time_keyboard=ot)
    kb_start.add(*[types.KeyboardButton(name) for name in m])
    return kb_start


def is_url(url):
    return urlparse(url).scheme != ""


def make_page(item):
        # Generate Tepegraph Page
        html_page = '<figure><img src="%s" alt="%s" /></figure><ul>%s</ul><blockquote>%s</blockquote><h3>Оставь заявку</h3><blockquote>Москва: +7 499 110-90-10</blockquote><blockquote>Санкт-Петербург: +7 812 458-44-44</blockquote><blockquote>Написать в ВК чате: <a href="https://goo.gl/CcPfmM">vk.me/putevka.travel</a></blockquote>' % (
            item['image_url'],
            item['name'], "".join(["<li>%s</li>" % x for x in item['hotels']]),
            item['conditions']
        )

        t = telegraph.createAccount(short_name="Putevka.Travel", author_name='Putevka.Travel', author_url='http://t.me/%s' % channel_name)
        page = telegraph.createPage(
            title='%s' % item['name'],
            author_name=t['author_name'],
            author_url=t['author_url'],
            html_content=html_page
        )

        petegraph_url = 'http://telegra.ph/{}'.format(page['path'])

        return petegraph_url


def _name(name='', tour_id=''):
    try:
        title = name.rsplit(',', 1)[0].replace('`', '\'').replace('*', '✮').strip()
        price = [x.strip('. ').replace(' ', ' ') for x in name.rsplit(',', 1)[1].replace('вместо', 'место').split('место')]
        return [title] + [price[0]] + [price[1]]
    except:
        return None


def stripe(string):
    return string.replace(' ', '').replace('1', '1̶').replace('2', '2̶').replace('3', '3̶').replace('4', '4̶').replace('5', '5̶').replace('6', '6̶').replace('7', '7̶').replace('8', '8̶').replace('9', '9̶').replace('0', '0̶')


@bot.message_handler(commands=["test"])
def test(message):
    check_new_item(message.chat.id)
    return 0


check_new_item()

scheduler.start()
scheduler.add_job(check_new_item, trigger='interval', minutes=10)

bot.polling()

# if __name__ == '__main__':
#     bot.polling()
#     scheduler.start()
#     bot.polling(none_stop=True)
