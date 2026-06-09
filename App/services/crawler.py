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
    raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in the .env file!")

API_ID = int(API_ID)
db = get_db()

TARGET_CHANNELS = [
    "@rentalgram",
    "@rentalbase",
    "@arearental",
    "@rentalentfess"
]


RAW_ALLOWED_WORDS = [
    "bxb", "gxg", "gxb", "mxm", "wxw", 
    "boyfriend", "girlfriend", "rent", "#aos", 
    "#findrent", "#afeksi", "#love", "male", "female", "boy", "boyfriend",
    "woman", "man", "girl", "girls", "bf", "gf"
]
ALLOWED_WORDS = [word.lower() for word in RAW_ALLOWED_WORDS]


RAW_EXCLUDED_WORDS = [
    "business", "trial", "tes", "promo","#post",
    "#explore", "#ads", "#follow", "#loveinfo", 
    "#findhouse", "#storyrent", "#keporent", 
    "#spillrent", "#rg", "#share", "#sharerent",
    "#qt", "#pt", "#askrent", "#mootsrent", 
    "#rentask", "#rentmoots", "#helprent", 
    "#rfpedia", "#woa", "#agencyship",
    "#seputarental", "#rbefriend", "confelove", 
    "confelov", "ketentuan", "menfess", "send", "@"
]
EXCLUDED_WORDS = [word.lower() for word in RAW_EXCLUDED_WORDS]

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
print("Crawler service initialized (Save All Raw Data + Filtered Analytics)...")

def data_crawler(text):
    text_lower = text.lower()
    extraction = "Relationship"
    if any(x in text_lower for x in ["bxb", "boyfriend", "boy", "male", "boys", "mxm", "bf"]):
        extraction = "Boyfriend"
    elif any(x in text_lower for x in ["gxg", "girlfriend", "girls", "woman", "wxw", "gxb", "gf"]):
        extraction = "Girlfriend"
    return extraction

async def process_and_save_message(msg, channel, is_realtime=False):
    # Validasi dasar: Pastikan ada teks di dalam pesan
    if not msg.text:
        return False

    try:
        # 1. Selalu perbarui info channel tempat pesan berasal
        db.rental_channels.update_one(
            {"channel_id": channel.id},
            {
                "$set": {
                    "channel_name": getattr(channel, 'title', 'Unknown'),
                    "username": f"@{channel.username}" if getattr(channel, 'username', None) else str(channel.id),
                    "last_crawled": datetime.datetime.now(datetime.timezone.utc),
                }
            },
            upsert=True,
        )

        # 2. AKSI LANGSUNG: Simpan semua pesan baru ke tabel rental_posts tanpa filter!
        existing_post = db.rental_posts.find_one({"channel_id": channel.id, "message_id": msg.id})
        inserted_id = None
        
        if not existing_post:
            post_doc = {
                "channel_id": channel.id,
                "message_id": msg.id,
                "timestamp": msg.date,
                "raw_text": msg.text,
            }
            result = db.rental_posts.insert_one(post_doc)
            inserted_id = result.inserted_id
            
            if is_realtime:
                print(f"[RAW] Pesan baru otomatis masuk rental_posts | ID: {msg.id}")
        else:
            inserted_id = existing_post["_id"]

        text_lower = msg.text.lower()
        
        # Saringan A: Abaikan teks yang terlalu pendek (di bawah 30 karakter biasanya cuma spam/link pendek)
        if len(msg.text) <= 30:
            if is_realtime:
                print(f"   └─ [X] ANALYTICS SKIPPED: Teks terlalu pendek (ID: {msg.id})")
            return True

        # Saringan B: Cek Blacklist
        for word in EXCLUDED_WORDS:
            if word in text_lower:
                if is_realtime:
                    print(f"   └─ [X] ANALYTICS SKIPPED: Mengandung kata blacklist '{word}' (ID: {msg.id})")
                return True

        # Saringan C: Cek Whitelist
        if not any(word in text_lower for word in ALLOWED_WORDS):
            if is_realtime:
                print(f"   └─ [X] ANALYTICS SKIPPED: Tidak lolos kata kunci Whitelist (ID: {msg.id})")
            return True

        # 4. JIKA LOLOS SEMUA SARINGAN: Masukkan ke rental_analytics agar bisa dibaca Bot
        existing_analytics = db.rental_analytics.find_one({"post_id": inserted_id})
        
        if not existing_analytics:
            username_clean = getattr(channel, 'username', None)
            username_clean = username_clean if username_clean else str(channel.id)
            link_sumber = f"https://t.me/{username_clean}/{msg.id}"
            
            extraction = data_crawler(msg.text) 
            baris = [b.strip() for b in msg.text.split("\n") if b.strip()]
            Title = baris[0][:60] if baris else "Info"
            
            analytics_doc = {
                "post_id": inserted_id,
                "Info_Title": Title,
                "Relationship_Type": extraction,
                "source_link": link_sumber,
                "is_notified": False 
            }
            db.rental_analytics.insert_one(analytics_doc)
            
            tag = "[REAL-TIME]" if is_realtime else "[HISTORICAL]"
            print(f"{tag} [✓] LOLOS FILTER & MASUK ANALYTICS! | {getattr(channel, 'title', 'Unknown')} | ID: {msg.id}")
            
        return True

    except Exception as e:
        print(f"[-] Gagal memproses pesan ID {msg.id}: {e}")
        return False

async def handler_pesan_baru(event):
    channel = await event.get_chat()
    print(f"[NOTIF] Ada postingan baru masuk di Telegram dari: {getattr(channel, 'title', 'Unknown')} (ID Pesan: {event.message.id})")
    await process_and_save_message(event.message, channel, is_realtime=True)

async def main_crawler_flow():
    print("\n[*] Menghubungkan dan verifikasi target channels...")
    resolved_entities = []
    for ch in TARGET_CHANNELS:
        try:
            entity = await client.get_entity(ch)
            resolved_entities.append(entity)
            print(f"[✓] Terhubung ke channel: {getattr(entity, 'title', ch)} (ID: {entity.id})")
        except Exception as e:
            print(f"[X] Gagal mendaftarkan channel {ch}: {e}")

    if not resolved_entities:
        print("[-] Tidak ada channel yang berhasil terhubung. Proses dihentikan.")
        return

    print("\n[*] Memulai penarikan data lama (Historical Crawl)...")
    for entity in resolved_entities:
        try:
            print(f"[*] Scanning data lama di {entity.title}...")
            valid_count = 0
            async for msg in client.iter_messages(entity, limit=500):
                if valid_count >= 100:
                    break
                is_valid = await process_and_save_message(msg, entity, is_realtime=False)
                if is_valid:
                    valid_count += 1
            print(f"[V] Selesai scan {entity.title}! Saringan menghasilkan {valid_count} data valid.")
        except Exception as e:
            print(f"[X] Gagal melakukan data lama untuk {entity.title}: {e}")

    client.add_event_handler(handler_pesan_baru, events.NewMessage(chats=resolved_entities))
    print("\n[V] LIVE CRAWLER REAL-TIME AKTIF!")
    print("[*] Semua pesan baru otomatis masuk DB. Pesan valid otomatis dioper ke Bot. Pantau terminal...\n")

def run_crawler():
    print("Membuka koneksi Telethon Client...")
    client.start()
    client.loop.run_until_complete(main_crawler_flow())
    client.run_until_disconnected()

if __name__ == "__main__":
    run_crawler()