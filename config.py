# config.py
from os import environ

API_ID = int(environ.get("API_ID", ""))
API_HASH = environ.get("API_HASH", "")
BOT_TOKEN = environ.get("BOT_TOKEN", "")
MONGO_URI = environ.get("MONGO_URI", "")
OWNER_ID = int(environ.get("OWNER_ID", ""))
