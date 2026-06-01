# RentRadar

RentRadar is a Python-based automation system that combines a real-time Telegram crawler (scraper) with an interactive Telegram bot. The project is designed to monitor, collect, filter, classify, and deliver rental-related posts from multiple Telegram channels in real time, while storing all collected data in MongoDB for analysis and retrieval.

---

## Key Features

### Real-Time Message Monitoring

Uses Telethon with a strict entity binding approach to ensure that no new messages from monitored channels are missed.

### Hybrid Database Strategy

* Every incoming message is automatically backed up to the raw data collection (`rental_posts`).
* Messages that pass the filtering process are stored in the `rental_analytics` collection for bot consumption and analysis.

### Dual-Layer Smart Filtering

Applies both whitelist and blacklist filtering:

* Whitelist filters identify relevant rental-related content.
* Blacklist filters remove spam, advertisements, and unrelated posts.

### Automatic Rental Classification

Automatically categorizes rental posts into predefined types, such as:

* Boyfriend Rental
* Girlfriend Rental
* General Relationship Rental

### Live Broadcast Notifications

Instantly notifies all registered bot users whenever a new rental post passes the filtering process.

### On-Demand Search

Users can search for the latest and cleanest rental listings through Telegram groups or direct messages using the `/find` command.

---

## Technology Stack

### Programming Language

* Python 3.x

### Libraries

* Telethon (Telegram User API)
* PyTelegramBotAPI (Telegram Bot API)
* PyMongo

### Database

* MongoDB

### Deployment

* PM2
* Systemd

---

## Project Structure

```text
RentRadar/
│
├── databases/
│   └── mongo_service.py       # MongoDB connection and database services
│
├── crawler.py                 # Real-time scraping and filtering service
├── bot.py                     # Telegram bot and broadcast service
├── .env                       # Environment variables and API credentials
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

---

## How It Works

1. The crawler continuously monitors selected Telegram channels.
2. Every incoming message is stored in the raw database collection.
3. Messages are processed through whitelist and blacklist filters.
4. Relevant posts are classified and stored in the analytics collection.
5. Qualified rental posts are automatically broadcast to bot subscribers.
6. Users can search rental listings through Telegram commands in real time.

---

## Use Cases

* Rental listing aggregation
* Telegram channel monitoring
* Real-time content collection
* Data analytics and reporting
* Automated notification systems
* Community marketplace monitoring
