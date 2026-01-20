# bot.py
from keep_alive import keep_alive
keep_alive()

import discord
from discord.ext import commands, tasks
from dyktanda import DYKTANDA
import random
import datetime
import os
import pytz
import asyncpg

# ---- KONFIGURACJA ----
GODZINA = 16
MINUTA = 0
CWEL_CHANNEL_ID = 1303471531560796180
BOT_CHANNEL_ID = 1325976696788353165
DYKTANDO_CHANNEL_ID = 1325976696788353165
DYKTANDO_USER_ID = 807664458058825729
DYKTANDO_HOUR = 17
DYKTANDO_MINUTE = 40

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


# --- DB ---
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


# --- READY ---
@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")
    if DB_URL:
        await connect_db()
        await init_db()
        
krzelo_ping.start()
krzeloo_ping.start()
dyktando_ping.start()
planowany_ping.start()


# --- PLANOWANY CWEL ---
@tasks.loop(minutes=1)
async def planowany_ping():
    global last_pinged_user_id
    tz = pytz.timezone("Europe/Warsaw")
    now = datetime.datetime.now(tz)

    if now.hour == GODZINA and now.minute == MINUTA:
        channel = bot.get_channel(CWEL_CHANNEL_ID)
        if not channel:
            return

        members = [
            m for m in channel.guild.members
            if not m.bot and m.id != last_pinged_user_id
        ]

        if not members:
            return

        user = random.choice(members)
        last_pinged_user_id = user.id

        if db_pool:
            await update_ranking(user.id)

        await channel.send(f"{user.mention}, zostałeś wybrany na cwela dnia! 💀")


# --- !CWEL ---
@bot.command()
async def cwel(ctx):
    if ctx.channel.id != CWEL_CHANNEL_ID:
        return

    if ctx.author.id not in ALLOWED_USERS:
        await ctx.send("❌ Nie masz uprawnień!")
        return

    members = [m for m in ctx.guild.members if not m.bot]
    user = random.choice(members)

    if db_pool:
        await update_ranking(user.id)

    await ctx.send(f"{user.mention}, zostałeś wybrany na cwela dnia! 💀")


# --- RANKING ---
@bot.command()
async def ranking(ctx):
    if not db_pool:
        return

    top = await load_top_n(10)
    lines = []

    for i, (uid, count) in enumerate(top, 1):
        user = await bot.fetch_user(uid)
        lines.append(f"{i}. {user.name} - {count}")

    await ctx.send("🏆 Ranking cweli dnia:\n" + "\n".join(lines))


# --- KRZEŁO DO ROBOTY ---
@tasks.loop(minutes=1)
async def krzelo_ping():
    tz = pytz.timezone("Europe/Warsaw")
    now = datetime.datetime.now(tz)

    if now.weekday() < 5 and now.hour == 4 and now.minute == 0:
        channel = bot.get_channel(BOT_CHANNEL_ID)
        user = await bot.fetch_user(1384921756313063426)
        await channel.send(f"{user.mention} Wstawaj Krzeło! 🧑‍🦽‍➡️")


# --- KRZEŁO Z ROBOTY ---
@tasks.loop(minutes=1)
async def krzeloo_ping():
    tz = pytz.timezone("Europe/Warsaw")
    now = datetime.datetime.now(tz)

    if now.weekday() < 5 and now.hour == 20 and now.minute == 0:
        channel = bot.get_channel(BOT_CHANNEL_ID)
        user = await bot.fetch_user(1384921756313063426)
        await channel.send(f"{user.mention} Gratulacje! 🧑‍🦽‍➡️")

# --- DAMIAN ---
@tasks.loop(minutes=1)
async def dyktando_ping():
    tz = pytz.timezone("Europe/Warsaw")
    now = datetime.datetime.now(tz)

    if now.hour == DYKTANDO_HOUR and now.minute == DYKTANDO_MINUTE:
        channel = bot.get_channel(DYKTANDO_CHANNEL_ID)
        if not channel:
            print("❌ Nie znaleziono kanału.")
            return

        user = await bot.fetch_user(DYKTANDO_USER_ID)
        tekst = random.choice(DYKTANDA)

        await channel.send(
            f"{user.mention}\n{tekst}",
            allowed_mentions=discord.AllowedMentions(users=True)
        )

# --- WIADOMOŚCI ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    await bot.process_commands(message)
    content = message.content.lower().strip()

    # --- SMAKI ---
    if message.channel.id == CWEL_CHANNEL_ID and content == "smaki":
        if message.author.id not in ALLOWED_USERS:
            await message.channel.send("❌ Nie masz uprawnień do używania tej komendy!")
            return

        procent = random.randint(0, 100)
        await message.channel.send(
            f"Dzisiaj procent smaczków na tytany wynosi: {procent}% 🍬"
        )
        return

    if message.channel.id != BOT_CHANNEL_ID:
        return

    if content == "igor":
        await message.channel.send(file=discord.File("igor.gif"))


# --- START ---
token = os.getenv("TOKEN")
bot.run(token)
