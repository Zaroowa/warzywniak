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

# ---------------- CONFIG ----------------
GODZINA = 16
MINUTA = 0

CWEL_CHANNEL_ID = 1303471531560796180
BOT_CHANNEL_ID = 1325976696788353165
DYKTANDO_CHANNEL_ID = 1325976696788353165

DYKTANDO_USER_ID = 807664458058825729
DYKTANDO_HOUR = 18
DYKTANDO_MINUTE = 0

KRZELO_ID = 1384921756313063426

ALLOWED_USERS = [
    630387902211162122, 388975847396081675, 304303798766010369,
    495334844088451083, 1253834602724982785, 714341935363391532,
    703166818847555605, 319810513536286720
]

# ---------------- BOT ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_URL = os.getenv("DATABASE_URL")
db_pool = None
last_pinged_user_id = None

# ---------------- HELPERS ----------------
def get_now():
    return datetime.datetime.now(pytz.timezone("Europe/Warsaw"))

async def send_ping(channel_id, target_id, text, image_path=None):
    channel = bot.get_channel(channel_id)
    if not channel:
        print("❌ Nie znaleziono kanału.")
        return

    target = await bot.fetch_user(target_id)

    if image_path and os.path.exists(image_path):
        await channel.send(
            f"{target.mention} {text}",
            file=discord.File(image_path),
            allowed_mentions=discord.AllowedMentions(users=True)
        )
    else:
        await channel.send(
            f"{target.mention} {text} (brak obrazka)",
            allowed_mentions=discord.AllowedMentions(users=True)
        )

async def choose_random_member(guild, exclude_id=None):
    members = [m for m in guild.members if not m.bot and m.id != exclude_id]
    if not members:
        members = [m for m in guild.members if not m.bot]
    return random.choice(members) if members else None

# ---------------- DATABASE ----------------
async def connect_db():
    global db_pool
    if DB_URL and db_pool is None:
        db_pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=5)

async def init_db():
    if not db_pool:
        return
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ranking (
                user_id BIGINT PRIMARY KEY,
                count INT DEFAULT 0
            )
        """)

async def update_ranking(user_id: int):
    if not db_pool:
        return
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO ranking (user_id, count)
            VALUES ($1, 1)
            ON CONFLICT (user_id)
            DO UPDATE SET count = ranking.count + 1
        """, user_id)

async def load_top_n(n=10):
    if not db_pool:
        return []
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, count FROM ranking ORDER BY count DESC LIMIT $1", n
        )
        return [(r["user_id"], r["count"]) for r in rows]

# ---------------- TASKS ----------------
@tasks.loop(minutes=1)
async def planowany_ping():
    global last_pinged_user_id
    now = get_now()

    if now.hour == GODZINA and now.minute == MINUTA:
        channel = bot.get_channel(CWEL_CHANNEL_ID)
        if not channel:
            return

        user = await choose_random_member(channel.guild, last_pinged_user_id)
        if not user:
            return

        last_pinged_user_id = user.id
        await update_ranking(user.id)
        await channel.send(f"{user.mention}, zostałeś wybrany na cwela dnia! 💀")

# 🔔 4:00
@tasks.loop(minutes=1)
async def krzelo_ping():
    now = get_now()
    if now.weekday() < 5 and now.hour == 4 and now.minute == 0:
        await send_ping(
            BOT_CHANNEL_ID,
            KRZELO_ID,
            "Wstawaj Krzeło! Dzisiaj tylko 16h do odjebania za najniższą krajową! 🧑‍🦽‍➡️",
            "adios.png"
        )

# 🔔 20:00
@tasks.loop(minutes=1)
async def krzeloo_ping():
    now = get_now()
    if now.weekday() < 5 and now.hour == 20 and now.minute == 0:
        await send_ping(
            BOT_CHANNEL_ID,
            KRZELO_ID,
            "Gratulacje! Właśnie odjebałeś podwójną zmianę jak typowy ukr! 🧑‍🦽‍➡️",
            "krzeloo.png"
        )

@tasks.loop(minutes=1)
async def dyktando_ping():
    now = get_now()
    if now.hour == DYKTANDO_HOUR and now.minute == DYKTANDO_MINUTE:
        channel = bot.get_channel(DYKTANDO_CHANNEL_ID)
        if not channel:
            return

        user = await bot.fetch_user(DYKTANDO_USER_ID)
        tekst = random.choice(DYKTANDA)
        await channel.send(
            f"{user.mention}\n{tekst}",
            allowed_mentions=discord.AllowedMentions(users=True)
        )

# ---------------- EVENTS & COMMANDS ----------------
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

@bot.command()
async def ranking(ctx):
    top = await load_top_n(10)
    if not top:
        return
    lines = []
    for i, (uid, count) in enumerate(top, 1):
        user = await bot.fetch_user(uid)
        lines.append(f"{i}. {user.name} - {count}")
    await ctx.send("🏆 Ranking cweli dnia:\n" + "\n".join(lines))

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    await bot.process_commands(message)
    content = message.content.lower().strip()

    if message.channel.id == CWEL_CHANNEL_ID and content == "smaki":
        if message.author.id not in ALLOWED_USERS:
            await message.channel.send("❌ Nie masz uprawnień!")
            return
        await message.channel.send(
            f"Dzisiaj procent smaczków na tytany wynosi: {random.randint(0,100)}% 🍬"
        )

    if message.channel.id == BOT_CHANNEL_ID and content == "igor":
        await message.channel.send(file=discord.File("igor.gif"))

# ---------------- START ----------------
bot.run(os.getenv("TOKEN"))
