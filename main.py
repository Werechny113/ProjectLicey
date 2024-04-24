import sqlite3
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

connection = sqlite3.connect("cafe.db")
cursor = connection.cursor()

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()

bot = Bot(token="6658495650:AAG4a33uPqI7MisncshXGu6BNfAFUiNbL7E")
dp = Dispatcher(bot, storage=storage)