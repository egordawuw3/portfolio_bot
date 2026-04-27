import aiosqlite
import logging
from config import DB_NAME

logger = logging.getLogger("KK_Bot.DB")

class Database:
    def __init__(self):
        self.conn = None

    async def connect(self):
        self.conn = await aiosqlite.connect(DB_NAME)
        await self.conn.execute('PRAGMA journal_mode=WAL;') 
        await self.conn.execute('PRAGMA synchronous=NORMAL;')
        await self.conn.execute('''CREATE TABLE IF NOT EXISTS users 
                         (user_id INTEGER PRIMARY KEY, username TEXT, join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        await self.conn.execute('''CREATE TABLE IF NOT EXISTS orders 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, 
                          service TEXT, task TEXT, phone TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        await self.conn.commit()

    async def add_user(self, user_id: int, username: str):
        await self.conn.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        await self.conn.commit()

    async def insert_order(self, uid: int, username: str, service: str, task: str, phone: str):
        await self.conn.execute("INSERT INTO orders (user_id, username, service, task, phone) VALUES (?, ?, ?, ?, ?)",
                                (uid, username, service, task, phone))
        await self.conn.commit()
        logger.info(f"✅ В БД добавлен лид: @{username} | {service}")

    async def get_all_users(self):
         async with self.conn.execute("SELECT user_id FROM users") as cursor:
            return [row[0] for row in await cursor.fetchall()]

    async def get_stats(self):
        async with self.conn.execute("SELECT COUNT(*) FROM users") as cur: u_count = (await cur.fetchone())[0]
        async with self.conn.execute("SELECT COUNT(DISTINCT user_id) FROM orders") as cur: o_count = (await cur.fetchone())[0]
        async with self.conn.execute("SELECT COUNT(*) FROM orders WHERE date(created_at) = date('now', 'localtime')") as cur: t_count = (await cur.fetchone())[0]
        return u_count, o_count, t_count

    async def close(self):
        if self.conn: await self.conn.close()

db = Database()
