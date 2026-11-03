import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "eaaxw")
WEB_SECRET_KEY = os.getenv("WEB_SECRET_KEY", "your-secret-key-change-this")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
