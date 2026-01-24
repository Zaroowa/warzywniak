import asyncpg
import os

DB_URL = os.getenv("DATABASE_URL")
db_pool = None

async def connect_db():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=5)

async def init_db():
    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS ranking (
            user_id BIGINT PRIMARY KEY,
            count INT DEFAULT 0
        )
        """)

async def update_ranking(user_id: int):
    async with db_pool.acquire() as conn:
        await conn.execute("""
        INSERT INTO ranking (user_id, count)
        VALUES ($1, 1)
        ON CONFLICT (user_id)
        DO UPDATE SET count = ranking.count + 1
        """, user_id)

async def load_top_n(n=10):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, count FROM ranking ORDER BY count DESC LIMIT $1", n
        )
        return [(r["user_id"], r["count"]) for r in rows]
