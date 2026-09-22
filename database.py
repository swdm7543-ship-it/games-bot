import aiosqlite

DB_PATH = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS points (
                user_id INTEGER,
                guild_id INTEGER,
                game TEXT,
                points INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                plays INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id, game)
            )
        """)
        await db.commit()

async def add_points(user_id, guild_id, game, amount, won=False):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO points (user_id, guild_id, game, points, wins, plays)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(user_id, guild_id, game) DO UPDATE SET
                points = points + excluded.points,
                wins = wins + excluded.wins,
                plays = plays + 1
        """, (user_id, guild_id, game, amount, 1 if won else 0))
        await db.commit()

async def get_total_points(user_id, guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COALESCE(SUM(points),0) FROM points WHERE user_id=? AND guild_id=?",
            (user_id, guild_id)
        ) as cur:
            row = await cur.fetchone()
            return row[0]

async def get_leaderboard(guild_id, game=None, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        if game:
            q = """SELECT user_id, SUM(points), SUM(wins)
                   FROM points WHERE guild_id=? AND game=?
                   GROUP BY user_id ORDER BY SUM(points) DESC LIMIT ?"""
            params = (guild_id, game, limit)
        else:
            q = """SELECT user_id, SUM(points), SUM(wins)
                   FROM points WHERE guild_id=?
                   GROUP BY user_id ORDER BY SUM(points) DESC LIMIT ?"""
            params = (guild_id, limit)
        async with db.execute(q, params) as cur:
            return await cur.fetchall()

async def get_stats(user_id, guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT game, points, wins, plays FROM points WHERE user_id=? AND guild_id=?",
            (user_id, guild_id)
        ) as cur:
            return await cur.fetchall()
