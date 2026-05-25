import asyncio
import datetime
import os

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from databases.mongo_service import get_db

load_dotenv()
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING")

if not API_ID or not API_HASH:
    raise ValueError(
        "TELEGRAM_API_ID atau TELEGRAM_API_HASH tidak ditemukan di file .env!"
    )


API_ID = int(API_ID)
db = get_db()
TARGET_CHANNELS = [
    "@infoBeasiswaIDN",
    "@Beasiswaindo",
    "@scholarship4us",
    "@scholarship",
]
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


def ekstrak_beasiswa(text):
    text_lower = text.lower()
    jenjang = "Umum"
    if any(x in text_lower for x in ["s1", "sarjana", "bachelor", "undergraduate"]):
        jenjang = "S1"
    elif any(x in text_lower for x in ["s2", "magister", "master", "postgraduate"]):
        jenjang = "S2"
    elif any(x in text_lower for x in ["s3", "doktor", "phd"]):
        jenjang = "S3"
    elif any(x in text_lower for x in ["sma", "smk", "pelajar"]):
        jenjang = "SMA/Sederajat"

    lokasi = "Dalam Negeri"
    luar_negeri_keywords = [
        "luar negeri",
        "internasional",
        "international",
        "inggris",
        "australia",
        "jepang",
        "amerika",
        "uk",
        "usa",
        "eropa",
    ]
    if any(keyword in text_lower for keyword in luar_negeri_keywords):
        lokasi = "Luar Negeri"

    return jenjang, lokasi

async def proses_crawling():
    print("Crawling scholarship channels...")

    for channel in TARGET_CHANNELS:
        try:
            entity = await client.get_entity(channel)

            db.scholarship_channels.update_one(
                {"channel_id": entity.id},
                {
                    "$set": {
                        "channel_name": entity.title,
                        "username": channel,
                        "last_crawled": datetime.datetime.now(datetime.timezone.utc),
                    }
                },
                upsert=True,
            )
            print(f"\n[+] Crawling channel: {entity.title}")

            messages = await client.get_messages(entity, limit=100)
            data_masuk = 0

            for msg in messages:
                if msg.message and len(msg.message) > 50:
                    existing_post = db.scholarship_posts.find_one(
                        {"channel_id": entity.id, "message_id": msg.id}
                    )
                    if not existing_post:
                        post_doc = {
                            "channel_id": entity.id,
                            "message_id": msg.id,
                            "timestamp": msg.date,
                            "raw_text": msg.message,
                        }
                        result = db.scholarship_posts.insert_one(post_doc)
                        jenjang, lokasi = ekstrak_beasiswa(msg.message)
                        baris = [
                            b.strip() for b in msg.message.split("\n") if b.strip()
                        ]
                        judul_beasiswa = baris[0][:60] if baris else "Info Scholarship"
                        analytics_doc = {
                            "post_id": result.inserted_id,
                            "scholarship_title": judul_beasiswa,
                            "degree_level": jenjang,
                            "location_type": lokasi,
                        }
                        db.scholarship_analytics.insert_one(analytics_doc)
                        data_masuk += 1
            print(f"--> {data_masuk} Info Scholarship newly added")
        except Exception as e:
            print(f"[-] Failed to process {channel}: {e}")

    print("\n[V] Crawling Completed!")


def run_crawler():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    with client:
        loop.run_until_complete(proses_crawling())


if __name__ == "__main__":
    run_crawler()
