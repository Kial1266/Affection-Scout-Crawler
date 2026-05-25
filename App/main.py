import os
import sys
import threading

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import services.crawler
import services.services_bot


def jalankan_bot():
    print("Prepare to run the Telegram Bot...")
    services.services_bot.run_bot()


def jalankan_crawler():
    print("Prepare to run the Crawler...")
    services.crawler.run_crawler()


if __name__ == "__main__":
    print("Starting the application...")

    thread_bot = threading.Thread(target=jalankan_bot, name="Thread-Bot")
    thread_bot.start()
    print("Telegram Bot is running in a separate thread.")

    jalankan_crawler()
    print("\nCrawler completed its task.")
