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


@dp.message_handler(text=['Повара'])
async def cooks(message: types.Message):
    cooks = cursor.execute("SELECT * FROM cooks").fetchall()
    text = "Наши повара:\n"
    for cook in cooks:
        text += f"{cook[0]}: {cook[1]} - {cook[2]}, {cook[3]} лет\n"
    await bot.send_message(chat_id=message.from_user.id,
                           text=text)


@dp.message_handler(text=['Адрес'])
async def address(message: types.Message):
    await bot.send_location(chat_id=message.from_user.id,
                            latitude=51.635685,
                            longitude=39.248621)
    await bot.send_message(chat_id=message.from_user.id,
                           text="Название - Сели-поели")


@dp.message_handler(text=['Информация'])
async def general(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id,
                           text="Директор - Вася Пупкин, гений, миллиардер, плейбой, филантроп\n"
                                "Контактный номер - 88005553535\n"
                                "Работаем с 10 до 10")


@dp.message_handler(text=['Главное меню'])
async def back(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    about = types.KeyboardButton("О нас")
    menu = types.KeyboardButton("Меню")
    backet = types.KeyboardButton("Корзина")
    keyboard.add(about, menu, backet)

    await bot.send_message(chat_id=message.from_user.id,
                           text="Вы вернулись в главное меню",
                           reply_markup=keyboard)


@dp.message_handler(text=['Меню'])
async def menu(message: types.Message):
    delete = types.ReplyKeyboardRemove()
    food = cursor.execute("SELECT * FROM menu").fetchall()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for row in food:
        button = types.InlineKeyboardButton(text=row[1], callback_data=f"food{row[1]}")
        keyboard.add(button)
    back = types.InlineKeyboardButton("Назад", callback_data="back")
    keyboard.add(back)
    await bot.send_message(chat_id=message.from_user.id,
                           text="Выберите блюдо",
                           reply_markup=delete)
    await bot.send_message(chat_id=message.from_user.id,
                           text="Блюда:",
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda mes: mes.data == "back")
async def back(callback: types.CallbackQuery):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    about = types.KeyboardButton("О нас")
    menu = types.KeyboardButton("Меню")
    backet = types.KeyboardButton("Корзина")
    keyboard.add(about, menu, backet)
    await bot.delete_message(chat_id=callback.from_user.id,
                             message_id=callback.message.message_id)
    await bot.send_message(chat_id=callback.from_user.id,
                           text="Вы вернулись в главное меню",
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda mes: mes.data[:4] == "food")
async def food(callback: types.CallbackQuery):
    food_name = callback.data[4:]
    food = cursor.execute("SELECT * FROM menu WHERE name == ?", (food_name,)).fetchall()[0]
    photo = types.InputFile(f"{food[-1]}")
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add{food_name}")
    keyboard.add(button)

    await bot.send_photo(chat_id=callback.from_user.id,
                         photo=photo,
                         caption=f"Название - {food[1]}\n"
                                 f"Время готовки - {food[2]}\n"
                                 f"Цена - {food[3]}\n"
                                 f"Вес - {food[4]}",
                         reply_markup=keyboard)


@dp.callback_query_handler(lambda mes: mes.data[:3] == "add")
async def add(callback: types.CallbackQuery):
    buyed = cursor.execute("SELECT buy FROM users WHERE tg = ?", (callback.from_user.id,)).fetchall()
    food = callback.data[3:]

    if not bool(len(buyed[0][0])):
        buyed[0] = [food, "1"]
        cursor.execute("UPDATE users SET buy = ? WHERE tg = ?", (str(buyed[0]), callback.from_user.id))
        connection.commit()

        buyed = cursor.execute("SELECT buy FROM users WHERE tg = ?", (callback.from_user.id,)).fetchall()

    else:
        names = set()
        for row in buyed[0][0].split("; "):
            row = literal_eval(row)
            names.add(row[0])
        if food in names:
            new = []
            for row in buyed[0][0].split("; "):
                row = literal_eval(row)
                num = int(row[1])
                if row[0] == food:
                    row[1] = f"{num + 1}"
                new.append(row)
            cursor.execute("UPDATE users SET buy = ? WHERE tg = ?", ("", callback.from_user.id,))
            connection.commit()

            for row in new:
                if new.index(row) == 0:
                    cursor.execute(f"UPDATE users SET buy = ? WHERE tg = ?", (str(row), callback.from_user.id,))
                else:
                    cursor.execute(f"UPDATE users SET buy = buy || ? WHERE tg = ?",
                                   ("; " + str(row), callback.from_user.id,))
                connection.commit()

        else:
            cook = [food, "1"]
            cursor.execute(f"UPDATE users SET buy = buy || ? WHERE tg = ?", ("; " + str(cook), callback.from_user.id,))
            connection.commit()

    stop = types.InlineKeyboardMarkup(row_width=1)
    btn = types.InlineKeyboardButton("Отменить", callback_data="stop")
    stop.add(btn)
    await bot.send_message(chat_id=callback.from_user.id,
                           text=f"Успешно добавлено блюдо: {callback.data[3:]}",
                           reply_markup=stop)


@dp.callback_query_handler(lambda mes: mes.data[:4] == "stop")
async def stop(callback: types.CallbackQuery):
    buyed = cursor.execute("SELECT buy FROM users WHERE tg = ?", (callback.from_user.id,)).fetchall()[0]

    if len(buyed[0].split("; ")) > 1:
        buy_all = []
        for row in buyed[0].split("; "):
            row = literal_eval(row)
            buy_all.append(row)
        buy_all.pop(-1)
        for row in buy_all:
            if buy_all.index(row) == 0:
                cursor.execute(f"UPDATE users SET buy = ? WHERE tg = ?", (str(row), callback.from_user.id,))
            else:
                cursor.execute(f"UPDATE users SET buy = buy || ? WHERE tg = ?",
                               ("; " + str(row), callback.from_user.id,))
            connection.commit()

    else:
        cursor.execute(f"UPDATE users SET buy = ? WHERE tg = ?", ("", callback.from_user.id,))
        connection.commit()
    await bot.delete_message(chat_id=callback.from_user.id,
                             message_id=callback.message.message_id)
    await bot.send_message(chat_id=callback.from_user.id,
                           text="Отменено")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
