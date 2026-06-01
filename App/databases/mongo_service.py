import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI tidak ditemukan di file .env!")

client = MongoClient(MONGO_URI)
db = client["rental_bot"]

def get_db():
    return db
