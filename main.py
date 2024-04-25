import sqlite3
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

connection = sqlite3.connect("cafe.db")
cursor = connection.cursor()

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()

bot = Bot(token="6658495650:AAG4a33uPqI7MisncshXGu6BNfAFUiNbL7E")
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'])
async def hello(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    about = types.KeyboardButton("О нас")
    menu = types.KeyboardButton("Меню")
    backet = types.KeyboardButton("Корзина")
    keyboard.add(about, menu, backet)

    if not bool(len(cursor.execute("SELECT * FROM users WHERE tg = ?",
                                   (message.from_user.id,)).fetchall())):
        cursor.execute("INSERT INTO users (tg) VALUES (?)", (message.from_user.id,))
        connection.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        first_button = types.KeyboardButton(text="📱 Отправить", request_contact=True)
        markup.add(first_button)

        await bot.send_message(chat_id=message.from_user.id,
                               text="Привет!\nЯ кафе, в котором ты можешь заказать вкусной еды",
                               reply_markup=markup)
        await bot.send_message(chat_id=message.from_user.id,
                               text="Отправь /help и узнай, как мной можно пользоваться :)")
    else:
        await bot.send_message(chat_id=message.from_user.id,
                               text="Вы меня перезагрузили",
                               reply_markup=keyboard)


@dp.message_handler(content_types=types.ContentTypes.CONTACT)
async def contact(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    about = types.KeyboardButton("О нас")
    menu = types.KeyboardButton("Меню")
    backet = types.KeyboardButton("Корзина")
    keyboard.add(about, menu, backet)

    await bot.send_message(chat_id=message.from_user.id,
                           text="Мы добавили ваш номер! На него будут производить заказ",
                           reply_markup=keyboard)
    cursor.execute("UPDATE users SET phone = ? WHERE tg = ?",
                   (message.contact.phone_number, message.from_user.id))
    connection.commit()
