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

@bot.message_handler(commands=['help'])
def send_help(message):
    teks = (
        "💕 *Rental Finder Bot Help* \n\n"
        "/start - Daftar/Mulai menerima notif otomatis\n"
        "/find [Type] - Cari data terbaru (Contoh: `/find Boyfriend`, '/find nsfw' atau `/find Girlfriend`)"
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

    input_user = teks_pesan[1] 
    
    display_type = "NSFW" if input_user.lower() == "nsfw" else input_user.capitalize()
    
    # Ambil data terbersih dan terbaru berdasarkan waktu kirim asli di Telegram
    pipeline = [
        # [PERBAIKAN 2]: Gunakan $regex dengan $options: "i" agar pencarian mengabaikan huruf besar/kecil
        {
            "$match": {
                "Relationship_Type": { "$regex": f"^{input_user}$", "$options": "i" }
            }
        },
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
        bot.reply_to(message, f"Tidak ada info valid terbaru untuk type *{display_type}*.", parse_mode="Markdown")
        return

    balasan = f"✨ *Daftar Rental {display_type}:* ✨\n\n"
    for channel, items in data_per_channel.items():
        balasan += f"📢 *Channel: @{channel}*\n"
        for index, item in enumerate(items, 1):
            judul_asli = item.get("Info_Title", "Relationship Info")
            link_sumber = item.get('source_link', 'https://t.me')
            judul_aman = judul_asli.replace("*", "").replace("_", " ").replace("[", "").replace("]", "")
            balasan += f"  {index}. [{judul_aman}]({link_sumber})\n"
        balasan += "\n" 
        
    bot.reply_to(message, balasan, parse_mode="Markdown", disable_web_page_preview=True)


@bot.message_handler(commands=['stats'])
def cek_stats(message):
    pipeline = [
        {"$group": {"_id": "$Relationship_Type", "total": {"$sum": 1}}}
    ]
    hasil = list(db.rental_analytics.aggregate(pipeline))
    
    if not hasil:
        bot.reply_to(message, "none")
        return

    teks = "*Statistik:*\n\n"
    for item in hasil:
        kategori = item['_id'] if item['_id'] else "Tanpa Kategori"
        jumlah = item['total']
        teks += f"▪️ *{kategori}*: {jumlah} data\n"
        
    bot.reply_to(message, teks, parse_mode="Markdown")

def run_bot():
    print("Starting Telegram Bot API...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    run_bot()