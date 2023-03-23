import time
import telebot
from telebot import types
from dotenv import load_dotenv
import praw
import os


load_dotenv()
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

reddit = praw.Reddit(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    user_agent=os.getenv('USER_AGENT'),
)
files = []
subscription_bool = True


@bot.message_handler(commands=['help'])
def helper(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_filered = types.KeyboardButton("/filered")
    btn_subsred = types.KeyboardButton("/subsred")
    markup.add(btn_filered, btn_subsred)
    bot.send_message(message.from_user.id, '/filered - посмотреть посты с файлами (фото и гифки) у любого сабреддита\n'
                                           '/subsred - подписаться на сабреддит, чтобы смотреть посты с файлами '
                                           '(фото и гифки)',
                     reply_markup=markup)


@bot.message_handler(commands=['filered'])
def file_red(message):
    bot.send_message(message.from_user.id, 'Напишите существующий саб, который хотите посмотреть!')
    bot.register_next_step_handler(message, category)


@bot.message_handler(commands=['subsred'])
def subs_red(message):
    bot.send_message(message.from_user.id, 'Напишите существующий саб, на который хотите подписаться!')
    bot.register_next_step_handler(message, subscription_red)


@bot.message_handler(content_types=['text'])
def text_mes(message):
    global subscription_bool
    if message.text == 'стоп':
        subscription_bool = False
        bot.send_message(message.from_user.id, 'Подписка остановлена!')
    else:
        bot.send_message(message.from_user.id, 'Я тебя не понимаю. Чтобы узнать команды напиши /help')


def subscription_red(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_stop = types.KeyboardButton('стоп')
    markup.add(btn_stop)
    bot.send_message(message.from_user.id, 'Чтобы отписаться напишите: "стоп"', reply_markup=markup)
    sub = message.text
    while subscription_bool:
        time.sleep(5)
        subreddit = reddit.subreddit(sub)
        subs = subreddit.new(limit=1)
        for submission in subs:
            if submission.id not in files:
                files.append(submission.id)
                if submission.url[-3:] in ['jpg', 'png']:
                    bot.send_photo(message.from_user.id, submission.url)
                if submission.url[-3:] == 'gif':
                    bot.send_video(message.from_user.id, submission.url)


def category(message):
    sub = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_hot = types.KeyboardButton("hot")
    btn_new = types.KeyboardButton("new")
    btn_top = types.KeyboardButton("top")
    markup.add(btn_hot, btn_new, btn_top)
    bot.send_message(message.from_user.id, 'Напишите категорию саба("hot", "new", "top"):', reply_markup=markup)
    bot.register_next_step_handler(message, quantity_files, sub)


def quantity_files(message, sub):
    red_category = message.text
    if red_category in ["hot", "new"]:
        bot.send_message(message.from_user.id, 'Хорошо. Напишите какое количество постов выложить?(только целое число)')
        bot.register_next_step_handler(message, check_quantity, sub, red_category)
    elif red_category == 'top':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_all = types.KeyboardButton("all")
        btn_hour = types.KeyboardButton("hour")
        btn_day = types.KeyboardButton("day")
        btn_week = types.KeyboardButton("week")
        btn_month = types.KeyboardButton("month")
        btn_year = types.KeyboardButton("year")
        markup.add(btn_all, btn_hour, btn_day, btn_week, btn_month, btn_year)
        bot.send_message(message.from_user.id, 'Выберите промежуток топа '
                                               '("all", "hour", "day", "week", "month", "year")', reply_markup=markup)
        bot.register_next_step_handler(message, check_top, sub, red_category)
    else:
        bot.send_message(message.from_user.id, f'Нужно правильно написать категорию из списка!')
        bot.register_next_step_handler(message, quantity_files, sub)


def check_top(message, sub, red_category):
    gap_top = message.text
    if gap_top in ["all", "hour", "day", "week", "month", "year"]:
        bot.send_message(message.from_user.id, 'Хорошо. Напишите какое количество постов выложить?(только целое число)')
        bot.register_next_step_handler(message, check_quantity, sub, red_category, gap_top)
    else:
        bot.send_message(message.from_user.id, f'Нужно правильно написать промежуток из списка!')
        bot.register_next_step_handler(message, check_top, sub, red_category)


def check_quantity(message, sub, red_category, gap_top=''):
    try:
        quantity = int(message.text)
        bot.send_message(message.from_user.id, f'Хорошо. Выведу {quantity} постов-файлов!')
        message_photo(message, sub=sub, quantity=quantity, red_category=red_category, gap_top=gap_top)
    except Exception:
        bot.send_message(message.from_user.id, f'Нужно написать целое число!')
        bot.register_next_step_handler(message, check_quantity, sub=sub)


def message_photo(message, sub, quantity, red_category, gap_top):
    try:
        subreddit = reddit.subreddit(sub)
        if red_category == 'top':
            subs = subreddit.top(time_filter=gap_top)
        elif red_category == 'new':
            subs = subreddit.new()
        elif red_category == 'hot':
            subs = subreddit.hot()
        counter = 0
        for submission in subs:
            try:
                if submission.url[-3:] in ['jpg', 'png']:
                    bot.send_photo(message.from_user.id, submission.url)
                    counter += 1
                if submission.url[-3:] == 'gif':
                    bot.send_video(message.from_user.id, submission.url)
                    counter += 1
                if counter == quantity:
                    break
            except Exception:
                print('Error')
        if counter != quantity:
            bot.send_message(message.from_user.id, 'В нужных форматах больше нет файлов!')
    except Exception:
        bot.send_message(message.from_user.id, 'Такого саба нет!')


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)