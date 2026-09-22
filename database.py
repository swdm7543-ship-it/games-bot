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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                guild_id INTEGER,
                item_id TEXT,
                game TEXT,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id, item_id)
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

async def deduct_points(user_id, guild_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COALESCE(SUM(points),0) FROM points WHERE user_id=? AND guild_id=?",
            (user_id, guild_id)
        ) as cur:
            row = await cur.fetchone()
            total = row[0]
        if total < amount:
            return False
        # نخصم من لعبة "wallet" الخاصة بالمتجر
        await db.execute("""
            INSERT INTO points (user_id, guild_id, game, points)
            VALUES (?, ?, 'wallet', ?)
            ON CONFLICT(user_id, guild_id, game) DO UPDATE SET
                points = points - ?
        """, (user_id, guild_id, -amount, amount))
        await db.commit()
        return True

async def get_total_points(user_id, guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COALESCE(SUM(points),0) FROM points WHERE user_id=? AND guild_id=? AND game != 'wallet'",
            (user_id, guild_id)
        ) as cur:
            row = await cur.fetchone()
            return row[0]

async def get_leaderboard(guild_id, game=None, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        if game:
            q = """SELECT user_id, SUM(points), SUM(wins) FROM points
                   WHERE guild_id=? AND game=? GROUP BY user_id
                   ORDER BY SUM(points) DESC LIMIT ?"""
            params = (guild_id, game, limit)
        else:
            q = """SELECT user_id, SUM(points), SUM(wins) FROM points
                   WHERE guild_id=? AND game != 'wallet' GROUP BY user_id
                   ORDER BY SUM(points) DESC LIMIT ?"""
            params = (guild_id, limit)
        async with db.execute(q, params) as cur:
            return await cur.fetchall()

async def get_leaderboard_plays(guild_id, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT user_id, SUM(plays) FROM points
            WHERE guild_id=? AND game != 'wallet'
            GROUP BY user_id ORDER BY SUM(plays) DESC LIMIT ?
        """, (guild_id, limit)) as cur:
            return await cur.fetchall()

async def get_stats(user_id, guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT game, points, wins, plays FROM points WHERE user_id=? AND guild_id=? AND game != 'wallet'",
            (user_id, guild_id)
        ) as cur:
            return await cur.fetchall()

async def add_item(user_id, guild_id, item_id, game, quantity=1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO inventory (user_id, guild_id, item_id, game, quantity)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, guild_id, item_id) DO UPDATE SET
                quantity = quantity + excluded.quantity
        """, (user_id, guild_id, item_id, game, quantity))
        await db.commit()

async def get_inventory(user_id, guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT item_id, game, quantity FROM inventory WHERE user_id=? AND guild_id=? AND quantity > 0",
            (user_id, guild_id)
        ) as cur:
            return await cur.fetchall()

async def has_item(user_id, guild_id, item_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT quantity FROM inventory WHERE user_id=? AND guild_id=? AND item_id=?",
            (user_id, guild_id, item_id)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

async def use_item(user_id, guild_id, item_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE inventory SET quantity = quantity - 1 WHERE user_id=? AND guild_id=? AND item_id=? AND quantity > 0",
            (user_id, guild_id, item_id)
        )
        await db.commit()
