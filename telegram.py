import configparser
from telethon.sync import TelegramClient
import codecs

config = configparser.ConfigParser()
config.read_file(codecs.open("config.ini", 'r', 'utf8'))
client = TelegramClient(config['Telegram']['number'], int(config['Telegram']['api_id']), config['Telegram']['api_hash'])
with client:
    print('Ready')
