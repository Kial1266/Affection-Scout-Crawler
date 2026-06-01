# RentRadar 

RentRadar adalah sistem otomatis berbasis Python yang menggabungkan **Real-time Telegram Crawler (Scraper)** dan **Interactive Telegram Bot Viewer**. Project ini dirancang khusus untuk memantau, menyalin (*crawl*), menyaring (*filter*), dan menyajikan data dari berbagai channel rental Telegram secara instan (real-time) ke dalam database MongoDB.

---

## Fitur Utama

* **Anti-Budeg Real-time Listener**: Menggunakan Telethon dengan metode *Strict Entity Binding* untuk memastikan tidak ada pesan baru dari channel target yang terlewat.
* **Hybrid Database Strategy**: 
    * Semua pesan baru yang masuk otomatis di-backup 100% ke dalam koleksi database mentah (`rental_posts`).
    * Pesan yang lolos saringan kata kunci dimasukkan ke koleksi `rental_analytics` untuk dikonsumsi oleh bot.
* **Dual-Layer Smart Filter**: Penyaringan ketat menggunakan sistem **Whitelist** (kata kunci yang dicari) dan **Blacklist** (menghindari spam/ads/OOT).
* **Auto Classification**: Mengklasifikasikan tipe rental secara otomatis (misal: *Boyfriend*, *Girlfriend*, atau *Relationship* umum).
* **Live Broadcast Notification**: Mengirimkan notifikasi langsung ke semua user bot begitu ada rental baru yang lolos filter.
* **On-Demand Search**: User dapat mencari data rental terbersih dan terbaru di dalam grup atau DM menggunakan command `/find`.

---

## Tech Stack

* **Language:** Python 3.x
* **Libraries:** Telethon (Userbot API), PyTelegramBotAPI (Bot API), PyMongo
* **Database:** MongoDB
* **Process Manager (Deployment):** PM2 / Systemd

---

## Struktur Project

```text
RentRadar/
│
├── databases/
│   └── mongo_service.py       # Koneksi ke database MongoDB
│
├── crawler.py                 # Service real-time scraper & filter data
├── bot.py                     # Service Telegram Bot & auto-broadcast
├── .env                       # Konfigurasi token & API (Secret)
├── requirements.txt           # Dependency library Python
└── README.md                  # Dokumentasi project