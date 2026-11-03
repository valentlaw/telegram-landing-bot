import aiosqlite
from datetime import datetime

class Database:
    def __init__(self, db_path="bot.db"):
        self.db_path = db_path
    
    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    price INTEGER DEFAULT 100,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS problem_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            default_categories = [
                ("роспись", "Профессиональная роспись и кастомизация", 500),
                ("обучение", "Обучающие материалы и курсы", 300),
                ("шаблоны", "Готовые шаблоны и гайды", 200),
                ("другое", "Другие услуги и запросы", 100)
            ]
            
            for name, desc, price in default_categories:
                await db.execute("""
                    INSERT OR IGNORE INTO categories (name, description, price)
                    VALUES (?, ?, ?)
                """, (name, desc, price))
            
            await db.commit()
    
    async def add_user(self, user_id: int, username: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id, username)
                VALUES (?, ?)
            """, (user_id, username))
            await db.commit()
    
    async def get_category_info(self, category_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT name, description, price FROM categories
                WHERE name = ?
            """, (category_name,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    
    async def get_all_categories(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM categories ORDER BY name") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def update_category(self, name: str, description: str, price: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE categories
                SET description = ?, price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (description, price, name))
            await db.commit()
    
    async def add_problem_report(self, user_id: int, text: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO problem_reports (user_id, text)
                VALUES (?, ?)
            """, (user_id, text))
            await db.commit()
    
    async def get_problem_reports(self, limit=50):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT pr.*, u.username
                FROM problem_reports pr
                LEFT JOIN users u ON pr.user_id = u.user_id
                ORDER BY pr.created_at DESC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users ORDER BY created_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
