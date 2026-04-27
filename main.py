import asyncio
import logging
import time

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import db
from handlers import admin, client, portfolio

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=0.5):
        self.limit = limit; self.caches = {}
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if not user: return await handler(event, data)
        now = time.time()
        if user.id in self.caches and (now - self.caches[user.id]) < self.limit:
            if event.callback_query: await event.callback_query.answer("⏳ Не так быстро...", show_alert=False)
            return
        self.caches[user.id] = now
        return await handler(event, data)

class ColorFormatter(logging.Formatter):
    cyan, green, yellow, red, reset = "\x1b[36;20m", "\x1b[32;20m", "\x1b[33;20m", "\x1b[31;20m", "\x1b[0m"
    FORMATS = {
        logging.DEBUG: cyan + "%(asctime)s [DEBUG] %(message)s" + reset,
        logging.INFO: green + "%(asctime)s [INFO] " + reset + "%(message)s",
        logging.WARNING: yellow + "%(asctime)s [WARNING] %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s [ERROR] %(message)s" + reset,
    }
    def format(self, record): return logging.Formatter(self.FORMATS.get(record.levelno), datefmt="%H:%M:%S").format(record)

logger = logging.getLogger("KK_Bot")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(ColorFormatter())
logger.addHandler(ch)
logging.getLogger("aiogram").setLevel(logging.WARNING)


async def main():
    bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(ThrottlingMiddleware(limit=0.5))
    
    config.reload_portfolio()

    dp.include_router(admin.router)
    dp.include_router(portfolio.router)
    dp.include_router(client.router)

    await db.connect()
    logger.info("🚀 Бот запущен! Архитектура оптимизирована.")
    
    await bot.delete_webhook(drop_pending_updates=True) 
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        logger.info("🛑 Бот остановлен.")

if __name__ == "__main__":
    asyncio.run(main())
