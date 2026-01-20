from keep_alive import keep_alive
keep_alive()

import discord
from discord.ext import commands, tasks
import random
import datetime
import os
import pytz
import asyncpg
from dyktanda import DYKTANDA

# ---- KONFIGURACJA ----
GODZINA = 16
MINUTA = 0
CWEL_CHANNEL_ID = 1303471531560796180
BOT_CHANNEL_ID = 1325976696788353165
DYKTANDO_CHANNEL_ID = 1325976696788353165
DYKTANDO_USER_ID = 807664458058825729
DYKTANDO_HOUR = 18
DYKTANDO_MINUTE = 10

ALLOWED_USERS = [
    630387902211162122, 388975847396081675, 304303798766010369,
    495334844088451083, 1253834602724982785, 714341935363391532,
    703166818847555605, 319810513536286720
]

# -----------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_URL = os.getenv("DATABASE_URL")
db_pool = None
last_pinged_user_id = None

# -----------------------
# HELPERS
# -----------------------
def get_now():
    tz = pytz.timezone("Europe/Warsaw")
    return datetime.datetime.now(tz)

async def choose_random_member(guild, exclude_id=None):
    members = [m for m in guild.members if not m.bot and m.id != exclude_id]
    if not members:
        members = [m for m in guild.members if not m.bot]
    return random.choice(members) if members else None

# -----------------------
# DATABASE
# -----------------------
async def connect_db():
    global db_pool
    if db_pool is None and DB_URL:
        db_pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=5)

async def init_db():
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ranking (
                    user_id BIGINT PRIMARY KEY,
                    count INT DEFAULT 0
                )
            """)

async def update_ranking(user_id: int):
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ranking (user_id, count) VALUES ($1, 1)
                ON CONFLICT (user_id)
                DO UPDATE SET count = ranking.count + 1
            """, user_id)

async def load_top_n(n=10):
    if db_pool:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_id, count FROM ranking ORDER BY count DESC LIMIT $1", n
            )
            return [(r["user_id"], r["count"]) for r in rows]
    return []

# -----------------------
# TASKS
# -----------------------
async def ping_member(channel_id, user_id, msg):
    channel = bot.get_channel(channel_id)
    if channel:
        user = await bot.fetch_user(user_id)
        await channel.send(f"{user.mention} {msg}")

@tasks.loop(minutes=1)
async def planowany_ping():
    global last_pinged_user_id
    now = get_now()
    if now.hour == GODZINA and now.minute == MINUTA:
        channel = bot.get_channel(CWEL_CHANNEL_ID)
        if not channel:
            return
        user = await choose_random_member(channel.guild, last_pinged_user_id)
        if user:
            last_pinged_user_id = user.id
            await update_ranking(user.id)
            await channel.send(f"{user.mention}, zostałeś wybrany na cwela dnia! 💀")

@tasks.loop(minutes=1)
async def krzelo_ping():
    now = get_now()
    if now.weekday() < 5 and now.hour == 4 and now.minute == 0:
        await ping_member(BOT_CHANNEL_ID, 1384921756313063426, "Wstawaj Krzeło! 🧑‍🦽‍➡️")

@tasks.loop(minutes=1)
async def krzeloo_ping():
    now = get_now()
    if now.weekday() < 5 and now.hour == 20 and now.minute == 0:
        await ping_member(BOT_CHANNEL_ID, 1384921756313063426, "Gratulacje! 🧑‍🦽‍➡️")

@tasks.loop(minutes=1)
async def dyktando_ping():
    now = get_now()
    if now.hour == DYKTANDO_HOUR and now.minute == DYKTANDO_MINUTE:
        channel = bot.get_channel(DYKTANDO_CHANNEL_ID)
        if channel:
            user = await bot.fetch_user(DYKTANDO_USER_ID)
            tekst = random.choice(DYKTANDA)
            await channel.send(f"{user.mention}\n{tekst}", allowed_mentions=discord.AllowedMentions(users=True))

# -----------------------
# EVENTS & COMMANDS
# -----------------------
@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f"✅ Zalogowano jako {bot.user}")
    await connect_db()
    await init_db()
    planowany_ping.start()
    krzelo_ping.start()
    krzeloo_ping.start()
    dyktando_ping.start()

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    await bot.process_commands(message)
    content = message.content.lower().strip()

    # SMAKI
    if message.channel.id == CWEL_CHANNEL_ID and content == "smaki":
        if message.author.id not in ALLOWED_USERS:
            await message.channel.send("❌ Nie masz uprawnień do używania tej komendy!")
            return
        await message.channel.send(f"Dzisiaj procent smaczków na tytany wynosi: {random.randint(0,100)}% 🍬")
        return

    # IGOR
    if message.channel.id == BOT_CHANNEL_ID and content == "igor":
        await message.channel.send(file=discord.File("igor.gif"))

# --- !CWEL ---
@bot.command()
async def cwel(ctx):
    if ctx.channel.id != CWEL_CHANNEL_ID:
        return
    if ctx.author.id not in ALLOWED_USERS:
        await ctx.send("❌ Nie masz uprawnień!")
        return
    user = await choose_random_member(ctx.guild)
    if user:
        await update_ranking(user.id)
        await ctx.send(f"{user.mention}, zostałeś wybrany na cwela dnia! 💀")

# --- !RANKING ---
@bot.command()
async def ranking(ctx):
    top = await load_top_n(10)
    lines = []
    for i, (uid, count) in enumerate(top, 1):
        user = await bot.fetch_user(uid)
        lines.append(f"{i}. {user.name} - {count}")
    await ctx.send("🏆 Ranking cweli dnia:\n" + "\n".join(lines))

# -----------------------
# START
# -----------------------
bot.run(os.getenv("TOKEN"))
