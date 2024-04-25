import sqlite3
import logging
from ast import literal_eval

import aiogram.types as types
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

connection = sqlite3.connect("cafe.db")
cursor = connection.cursor()

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()

bot = Bot(token="7140052703:AAF1-6I8OiiQg5CDI6yHe-RCxLlTHsHaOcM")
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


@dp.message_handler(text=['Корзина'])
async def backet(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back = types.KeyboardButton("Главное меню")
    keyboard.add(back)
    await bot.send_message(chat_id=message.from_user.id,
                           text="Вы перешли в корзину",
                           reply_markup=keyboard)

    phone = cursor.execute("SELECT phone FROM users WHERE tg = ?", (message.from_user.id,)).fetchall()[0]
    backet = cursor.execute("SELECT buy FROM users WHERE tg = ?", (message.from_user.id,)).fetchall()
    if not bool(len(backet[0][0])):
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"Ваш номер телефона - {phone[0]}\n"
                                    f"Ваш id - {message.from_user.id}\n\n"
                                    f"Ваша корзина пуста")
    else:
        buy_keyboard = types.InlineKeyboardMarkup(row_width=1)
        buy = types.InlineKeyboardButton("Оплатить", callback_data="buy")
        buy_keyboard.add(buy)

        text = "Ваша корзина покупок:\n"
        summ = 0
        time = []
        for row in backet[0][0].split("; "):
            row = literal_eval(row)
            food_name = row[0]
            much = int(row[1])
            food_info = cursor.execute("SELECT * FROM menu WHERE name = ?", (food_name,)).fetchall()[0][2:]
            text += f"{food_name}: x{much} - {int(food_info[1]) * much}руб\n"
            summ += int(food_info[1]) * much
            time.append(food_info[0])
        text += f"--------------------\n\n"
        text += f"Сумма заказа: {summ}руб\n"
        text += f"Ориентировочное время приготовления: {max(time)} минут"
        await bot.send_message(chat_id=message.from_user.id,
                               text=text,
                               reply_markup=buy_keyboard)


@dp.callback_query_handler(lambda mes: mes.data[:3] == "buy")
async def buy(callback: types.CallbackQuery):
    await bot.delete_message(chat_id=callback.from_user.id,
                             message_id=callback.message.message_id)
    await bot.send_message(chat_id=callback.from_user.id,
                           text="Вы успешно оплатили")
    cursor.execute("UPDATE users SET buy = ? WHERE tg = ?", ("", callback.from_user.id))
    connection.commit()

@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id,
                           text="Нажимай на кнопки и узнавай о нас\n"
                                "Для перезагрузки - /start")


@dp.message_handler(text=['О нас'])
async def about(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cooks = types.KeyboardButton("Повара")
    address = types.KeyboardButton("Адрес")
    general = types.KeyboardButton("Информация")
    back = types.KeyboardButton("Главное меню")
    keyboard.add(back, address, cooks, general)
    await bot.send_message(chat_id=message.from_user.id,
                           text="Выберите раздел",
                           reply_markup=keyboard)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
