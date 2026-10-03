import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SHOP_NAME = os.getenv("SHOP_NAME", "Lyorna").strip() or "Lyorna"
CURRENCY = os.getenv("CURRENCY", "₽").strip() or "₽"
DB_PATH = os.getenv("DB_PATH", "lyorna.db")

def parse_admins() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "")
    ids = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids

ADMIN_IDS = parse_admins()
