from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

load_dotenv()
API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH")


with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n--- COPY TEKS DI BAWAH INI ---")
    print(client.session.save())
    print("------------------------------")