import datetime
import os
import threading
import telebot
import time
import pytz

from dotenv import load_dotenv
from pymongo import MongoClient
from databases.mongo_service import get_db

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN tidak ditemukan di file .env!")

bot = telebot.TeleBot(TOKEN)
db = get_db()

print("Bot service initialized (Clean Data Viewer Mode)...")

def broadcast_notifikasi_otomatis():
    tz = pytz.timezone('Asia/Jakarta')

    try:
        result = db.rental_analytics.update_many(
            {"$or": [{"is_notified": False}, {"is_notified": {"$exists": False}}]},
            {"$set": {"is_notified": True}}
        )
        print(f"[*] Cleared {result.modified_count} old backlog messages on boot.")
    except Exception as e:
        print(f"[-] Gagal membersihkan backlog: {e}")

    while True:
        try:
            sekarang = datetime.datetime.now(tz)
            is_quiet_hours = sekarang.hour >= 22 or sekarang.hour < 7

            pipeline = [
                {"$match": {"is_notified": False}},
                {
                    "$lookup": {
                        "from": "rental_posts",
                        "localField": "post_id",
                        "foreignField": "_id",
                        "as": "post_detail"
                    }
                },
                {"$unwind": "$post_detail"},
                {"$sort": {"post_detail.timestamp": 1}} 
            ]
            new_extractions = list(db.rental_analytics.aggregate(pipeline))

            if not new_extractions:
                time.sleep(10)
                continue

            if is_quiet_hours:
                for info in new_extractions:
                    db.rental_analytics.update_one(
                        {"_id": info["_id"]},
                        {"$set": {"is_notified": True}} 
                    )
                print(f"[{sekarang.strftime('%H:%M:%S')}] Night Mode: {len(new_extractions)} log dilewati & dibersihkan.")
                time.sleep(60) # Cek lagi tiap 1 menit selama jam malam
                continue

            all_user = list(db.bot_users.find({}))
            if all_user:
                print(f"[BROADCAST] Menyiarkan {len(new_extractions)} info rental live ke user!")
                
                for info in new_extractions:
                    db.rental_analytics.update_one(
                        {"_id": info["_id"]},
                        {"$set": {"is_notified": True}}
                    )

                    title = info.get("Info_Title", "Rental Info")
                    extraction = info.get("Relationship_Type", "Relationship")
                    link = info.get("source_link", "https://t.me")

                    judul_aman = title.replace("*", "").replace("_", " ").replace("[", "").replace("]", "")

                    pesan_notif = (
                        "*New! *\n\n"
                        f"*Title:* {judul_aman}\n"
                        f"*Type:* {extraction}\n\n"
                        f"👉 [Klik di Sini Untuk Melihat Source]({link})"
                    )
                    
                    for user in all_user:
                        try:
                            bot.send_message(user["chat_id"], pesan_notif, parse_mode='Markdown')
                        except Exception:
                            pass 
                    
                    time.sleep(120)

        except Exception as global_err:
            print(f"[-] Broadcast loop error: {global_err}")
            time.sleep(10)

# Jalankan thread
threading.Thread(target=broadcast_notifikasi_otomatis, daemon=True).start()

@bot.message_handler(commands=['help'])
def send_help(message):
    teks = (
        "💕 *Rental Finder Bot Help* \n\n"
        "/start - Daftar/Mulai menerima notif otomatis\n"
        "/find [Type] - Cari data terbaru (Contoh: `/find Boyfriend` atau `/find Girlfriend`)"
    )
    bot.reply_to(message, teks, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    db.bot_users.update_one(
        {"chat_id": message.chat.id},
        {"$set": {"username": message.from_user.username, "join_at": datetime.datetime.now()}},
        upsert=True
    )
    bot.reply_to(message, "Halo! Kamu berhasil terdaftar. Kamu akan otomatis dapat notifikasi begitu ada rental baru dirilis! 🔥")

@bot.message_handler(commands=["find"])
def find_relationship(message):
    teks_pesan = message.text.split()
    if len(teks_pesan) < 2:
        bot.reply_to(message, "Format salah! Gunakan contoh: `/find Boyfriend` atau `/find Girlfriend`", parse_mode="Markdown")
        return

    rentaltype = teks_pesan[1].capitalize() 
    
    # Ambil data terbersih dan terbaru berdasarkan waktu kirim asli di Telegram
    pipeline = [
        {"$match": {"Relationship_Type": rentaltype}},
        {
            "$lookup": {
                "from": "rental_posts",
                "localField": "post_id",
                "foreignField": "_id",
                "as": "post_detail"
            }
        },
        {"$unwind": "$post_detail"},
        {"$sort": {"post_detail.timestamp": -1}},  
        {"$limit": 100} 
    ]
    
    result = list(db.rental_analytics.aggregate(pipeline))

    data_per_channel = {}
    for item in result:
        link_sumber = item.get('source_link', 'https://t.me')
        try:
            channel_name = link_sumber.split('/')[3]
        except IndexError:
            channel_name = "Unknown Channel"
            
        if channel_name not in data_per_channel:
            data_per_channel[channel_name] = []
            
        if len(data_per_channel[channel_name]) < 5:
            data_per_channel[channel_name].append(item)

    if not data_per_channel:
        bot.reply_to(message, f"Tidak ada info valid terbaru untuk type *{rentaltype}*.", parse_mode="Markdown")
        return

    balasan = f"✨ *Daftar Rental {rentaltype}:* ✨\n\n"
    for channel, items in data_per_channel.items():
        balasan += f"📢 *Channel: @{channel}*\n"
        for index, item in enumerate(items, 1):
            judul_asli = item.get("Info_Title", "Relationship Info")
            link_sumber = item.get('source_link', 'https://t.me')
            judul_aman = judul_asli.replace("*", "").replace("_", " ").replace("[", "").replace("]", "")
            balasan += f"  {index}. [{judul_aman}]({link_sumber})\n"
        balasan += "\n" 
        
    bot.reply_to(message, balasan, parse_mode="Markdown", disable_web_page_preview=True)

def run_bot():
    print("Starting Telegram Bot API...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    run_bot()