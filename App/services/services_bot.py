import datetime
import os
import threading
import telebot
import time

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

def broadcast_notifikasi_otomatis():
    while True:
        try:
            print("[*] Checking for new scholarships to notify...")
            
            beasiswa_baru = list(db.scholarship_analytics.find({
                "$or": [
                    {"is_notified": False},
                    {"is_notified": {"$exists": False}}
                ]
                }).sort([("_id", -1)]).limit(1))
            semua_user = list(db.bot_users.find({}))
                        
            if beasiswa_baru and semua_user:
                for info in beasiswa_baru:
                    judul_asli = info.get("scholarship_title", "Info Scholarship")
                    lokasi = info.get("location_type", "Umum")
                    jenjang = info.get("degree_level", "Umum")
                    link = info.get("source_link", "https://t.me")

                    judul_aman = (
                        judul_asli.replace("*", "")
                        .replace("_", " ")
                        .replace("[", "")
                        .replace("]", "")
                    )

                    pesan_notif = (
                        "*INFO BEASISWA BARU!*\n\n"
                        f"*Scholarship:* {judul_aman}\n"
                        f"*Degree Level:* {jenjang}\n"
                        f"*Location:* {lokasi}\n\n"
                        f"[Click Here to View Official Source]({link})"
                    )
                    
                    for user in semua_user:
                        try:
                            bot.send_message(user["chat_id"], pesan_notif, parse_mode='Markdown')
                        except Exception as e:
                            print(f"[-] Gagal ngirim ke {user['chat_id']}: {e}")
                    
                    db.scholarship_analytics.update_one(
                        {"_id": info["_id"]},
                        {"$set": {"is_notified": True}}
                    )
                    
        except Exception as global_err:
            print(f"[-] Error pada loop broadcast: {global_err}")
            
        time.sleep(7200)
threading.Thread(target=broadcast_notifikasi_otomatis, daemon=True).start()

@bot.message_handler(commands=['help'])
def send_help(message):
    teks = (
        "Hai! I'm a scholarship finder bot:\n\n"
        "/start - Start the bot.\n"
        "/find [jenjang] - Find scholarships by degree level (example: `/find S1`).\n\n"
        "Usage:\n"
        "`/find S1` - Show scholarships for S1 level.\n\n"
        "_Data provided by our MongoDB crawler._"
    )
    bot.reply_to(message, teks, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    db.bot_users.update_one(
        {"chat_id": message.chat.id},
        {"$set": {"username": message.from_user.username, "join_at": datetime.datetime.now()}},
        upsert=True
    )
    
    teks = "Halo! You've been added to the user list. You will get notifications for new scholarships automatically! 🎓"
    bot.reply_to(message, teks)

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
            f"There's no scholarship info for *{jenjang_target}*. Try another degree level!",
            parse_mode="Markdown",
        )
        return

    balasan = f"*Top 10 scholarships for {jenjang_target}:*\n\n"
    for index, item in enumerate(hasil_list, 1):
        judul_asli = item.get("scholarship_title", "Beasiswa")
        link_sumber = item.get('source_link', 'https://t.me')
        judul_aman = (
            judul_asli.replace("*", "")
            .replace("_", " ")
            .replace("[", "")
            .replace("]", "")
        )
        balasan += f"*{index}. {judul_aman}*\n"
        balasan += f"Link: [Sumber Resmi]({link_sumber})\n\n"
        
    balasan += "\n_Data provided by our MongoDB crawler._"
    bot.reply_to(message, balasan, parse_mode="Markdown")

def run_bot():
    print("Starting the bot...")
    bot.infinity_polling()

if __name__ == "__main__":
    run_bot()