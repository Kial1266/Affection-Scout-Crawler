import os

import telebot
from dotenv import load_dotenv
from pymongo import MongoClient

from databases.mongo_service import get_db

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN tidak ditemukan di file .env!")

bot = telebot.TeleBot(TOKEN)
db = get_db()

print("Bot service initialized...")


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    teks = (
        "Halo! I'm scholarship finder bot 🎓\n\n"
        "Type /find [jenjang] to find scholarships by degree level.\n"
        "Example: `/find S1`"
    )
    bot.reply_to(message, teks, parse_mode="Markdown")


@bot.message_handler(commands=["find"])
def cari_beasiswa(message):
    teks_pesan = message.text.split()

    if len(teks_pesan) < 2:
        bot.reply_to(
            message,
            "Fill the degree level!\nExample: `/find S1`",
            parse_mode="Markdown",
        )
        return

    jenjang_target = teks_pesan[1].upper()
    hasil_cari = db.scholarship_analytics.aggregate(
        [
            {"$match": {"degree_level": jenjang_target}},
            {"$sort": {"_id": -1}},
            {"$limit": 10},
        ]
    )

    hasil_list = list(hasil_cari)
    if not hasil_list:
        bot.reply_to(
            message,
            f"Theres no scholarship info for *{jenjang_target}*. Try another degree level!",
            parse_mode="Markdown",
        )
        return

    balasan = f"*Top 10 scholarships for {jenjang_target}:*\n\n"

    for index, item in enumerate(hasil_list, 1):
        judul_asli = item.get("scholarship_title", "Beasiswa")
        lokasi = item.get("location_type", "Umum")

        judul_aman = (
            judul_asli.replace("*", "")
            .replace("_", " ")
            .replace("[", "")
            .replace("]", "")
        )

        balasan += f"*{index}. {judul_aman}*\n"
        balasan += f"Tipe: {lokasi}\n"
        balasan += "------------------------\n"

    balasan += "\n_Data provided by our MongoDB crawler._"
    bot.reply_to(message, balasan, parse_mode="Markdown")

def run_bot():
    print("Starting the bot...")
    bot.infinity_polling()

if __name__ == "__main__":
    run_bot()
