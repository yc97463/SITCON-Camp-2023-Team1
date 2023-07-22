# This is a simple echo bot using the decorator mechanism.
# It echoes any incoming text messages.

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot.types import InlineQueryResultArticle, InputTextMessageContent
from telebot.util import quick_markup

from jsonIOHandler import JsonIOHandler
import json
import time
from datetime import datetime


with open("secret.json", "r", encoding="utf8") as jfile:
  secret = json.load(jfile)

API_TOKEN = secret['TOKEN']

bot = telebot.TeleBot(API_TOKEN)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
  bot.send_message(message.chat.id, "This is Competition bot, newest competition information for you.")

@bot.message_handler(commands=['subscribe'])
def subscribe(massage):
  pass

print(">> Bot Is Online <<")
bot.infinity_polling()