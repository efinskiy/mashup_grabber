import telebot
from utils import Mashup
import os
from alchemical import Alchemical

COOKIES = {'Session_id': os.environ.get('COOKIES')}
LOG_CHAT_ID = int(os.environ.get('LOG_CHAT_ID'))
TOKEN = os.environ.get('TOKEN')

bot = telebot.TeleBot(TOKEN)
mashup = Mashup(COOKIES)
db = Alchemical('sqlite:///bot.sqlite')

