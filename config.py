import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН")
ADMIN_ID = int(os.getenv("ADMIN_ID", 12345678)) 
GROUP_ID = int(os.getenv("GROUP_ID", ADMIN_ID)) 
REVIEWS_CHANNEL_ID = int(os.getenv("REVIEWS_CHANNEL_ID", -1003731688412)) 
CHANNEL_LINK = "https://t.me/kankdigital" 
DB_NAME = 'kk_agency_final.db'
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME", "kankdigital") 
WELCOME_BANNER = "AgACAgQAAxkBAAIBhmnNbWOYqEAfWEU2_aSWZuWLaq0VAAK_DWsbFGFwUld5bRg4e4kfAQADAgADdwADOgQ"

PROJECTS = {}

def reload_portfolio():
    global PROJECTS
    try:
        with open('portfolio.json', 'r', encoding='utf-8') as f:
            PROJECTS = json.load(f)
        logging.getLogger("KK_Bot").info("✅ JSON файл с портфолио успешно загружен/перезагружен.")
    except Exception as e:
        logging.getLogger("KK_Bot").error(f"❌ Ошибка загрузки portfolio.json: {e}")
        PROJECTS = {"sites": [], "bots": [], "apps": []}
