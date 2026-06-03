import os
import sys
import threading
from flask import Flask  

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import services.crawler
import services.services_bot

app = Flask('')

@app.route('/')
def home():
    return "RentRadar System is Alive and Running!"

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)


def jalankan_bot():
    print("[BOT] Prepare to run the Telegram Bot...")
    services.services_bot.run_bot()

def jalankan_crawler():
    print("[CRAWLER] Prepare to run the Crawler...")
    services.crawler.run_crawler()


if __name__ == "__main__":
    print("=== STARTING THE APPLICATION ===")

    # A. Jalankan Web Server Dummy di Background Thread
    print("[SYSTEM] Starting dummy web server for Render port binding...")
    thread_server = threading.Thread(target=run_dummy_server, name="Thread-Web-Server", daemon=True)
    thread_server.start()


    thread_bot = threading.Thread(target=jalankan_bot, name="Thread-Bot", daemon=True)
    thread_bot.start()
    print("[SYSTEM] Telegram Bot is running in a separate thread.")

    jalankan_crawler()
    print("\n[SYSTEM] Crawler execution finished/disconnected.")