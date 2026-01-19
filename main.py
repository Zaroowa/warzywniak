# bot.py
from keep_alive import keep_alive
keep_alive()

import discord
from discord.ext import commands, tasks
import random
import datetime
import asyncio
import os
import pytz
import asyncpg

# ---- KONFIGURACJA ----
GODZINA = 16  # godzina pingowania (24h)
MINUTA = 0    # minuta pingowania
CWEL_CHANNEL_ID = 1303471531560796180  # ← kanał, gdzie działa komenda !cwel
BOT_CHANNEL_ID = 1325976696788353165   # ← kanał, gdzie bot reaguje na wiadomości i pingi
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
if not DB_URL:
    print("⚠️ Nie znaleziono DATABASE_URL w zmiennych środowiskowych. Jeśli testujesz lokalnie, ustaw DATABASE_URL.")
db_pool: asyncpg.pool.Pool | None = None

last_pinged_user_id = None


# --- Połączenie z DB i inicjalizacja tabeli ---
async def connect_db():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=5)
        print("🔌 Połączono z bazą danych (pool utworzony).")


async def init_db():
    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS ranking (
            user_id BIGINT PRIMARY KEY,
            count INT DEFAULT 0
        )
        """)
        print("📦 Tabela 'ranking' sprawdzona/utworzona.")


# --- Funkcje operujące na DB ---
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
        rows = await conn.fetch("SELECT user_id, count FROM ranking ORDER BY count DESC LIMIT $1", n)
        return [(r['user_id'], r['count']) for r in rows]


# --- Events / Tasks ---
@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")
    if DB_URL:
        await connect_db()
        await init_db()
    else:
        print("⚠️ DATABASE_URL nie ustawione — bot będzie działać bez DB.")
    planowany_ping.start()
    krzelo_ping.start()
    krzeloo_ping.start()


# 🔄 Ping losowej osoby o określonej godzinie
@tasks.loop(minutes=1)
async def planowany_ping():
    global last_pinged_user_id
    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.datetime.now(tz)

    if now.hour == GODZINA and now.minute == MINUTA:
        channel = bot.get_channel(CWEL_CHANNEL_ID)
        if channel is None:
            print("❌ Nie znaleziono kanału do planowanego pinga.")
            return

        guild = channel.guild
        members = [m for m in guild.members if not m.bot and m.id != last_pinged_user_id]
        if not members:
            await channel.send("Brak użytkowników do pingnięcia.")
            return

        losowy = random.choice(members)
        last_pinged_user_id = losowy.id

        if db_pool:
            await update_ranking(losowy.id)

        await channel.send(f"{losowy.mention}, zostałeś wybrany na cwela dnia! 💀")


# 🔒 Komenda !cwel tylko w jednym kanale
@bot.command()
async def cwel(ctx):
    if ctx.channel.id != CWEL_CHANNEL_ID:
        return

    if ctx.author.id not in ALLOWED_USERS:
        await ctx.send("❌ Nie masz uprawnień do używania tej komendy!")
        return

    guild = ctx.guild
    members = [m for m in guild.members if not m.bot]
    if not members:
        await ctx.send("Brak użytkowników do pingnięcia.")
        return

    losowy = random.choice(members)

    if db_pool:
        await update_ranking(losowy.id)

    await ctx.send(f"{losowy.mention}, zostałeś wybrany na cwela dnia! 💀")


# 📊 Ranking
@bot.command()
async def ranking(ctx):
    if not db_pool:
        await ctx.send("Ranking niedostępny — brak połączenia z bazą.")
        return

    top = await load_top_n(10)
    if not top:
        await ctx.send("Brak danych w rankingu.")
        return

    lines = []
    for i, (user_id, count) in enumerate(top, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            lines.append(f"{i}. {user.name}#{user.discriminator} - {count} razy")
        except Exception:
            lines.append(f"{i}. {user_id} - {count} razy (nieznany użytkownik)")

    await ctx.send("🏆 Ranking cweli dnia:\n" + "\n".join(lines))


# 🔔 Ping o 4:00 w dni robocze
@tasks.loop(minutes=1)
async def krzelo_ping():
    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.datetime.now(tz)

    if now.weekday() < 5 and now.hour == 4 and now.minute == 0:
        channel = bot.get_channel(BOT_CHANNEL_ID)
        if channel is None:
            print("❌ Nie znaleziono kanału dla krzelo_ping.")
            return

        target_id = 1384921756313063426  # ID Krzeła
        target = await bot.fetch_user(target_id)
        image_path = "adios.png"

        if os.path.exists(image_path):
            await channel.send(
                f"{target.mention} Wstawaj Krzeło! Dzisiaj tylko 16h do odjebania za najniższą krajową! 🧑‍🦽‍➡️",
                file=discord.File(image_path),
                allowed_mentions=discord.AllowedMentions(users=True)
            )
        else:
            await channel.send(
                f"{target.mention} Wstawaj Krzeło! Dzisiaj tylko 16h do odjebania za najniższą krajową! (brak obrazka) 🧑‍🦽‍➡️",
                allowed_mentions=discord.AllowedMentions(users=True)
            )


# 🔔 Ping o 20:00 w dni robocze
@tasks.loop(minutes=1)
async def krzeloo_ping():
    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.datetime.now(tz)

    if now.weekday() < 5 and now.hour == 20 and now.minute == 0:
        channel = bot.get_channel(BOT_CHANNEL_ID)
        if channel is None:
            print("❌ Nie znaleziono kanału dla krzeloo_ping.")
            return

        target_id = 1384921756313063426  # ID Krzeła
        target = await bot.fetch_user(target_id)
        image_path = "krzeloo.png"

        if os.path.exists(image_path):
            await channel.send(
                f"{target.mention} Gratulacje! Właśnie odjebałeś podwójną zmianę jak typowy ukr! 🧑‍🦽‍➡️",
                file=discord.File(image_path),
                allowed_mentions=discord.AllowedMentions(users=True)
            )
        else:
            await channel.send(
                f"{target.mention} Gratulacje! Właśnie odjebałeś podwójną zmianę jak typowy ukr! 🧑‍🦽‍➡️ (brak obrazka) ",
                allowed_mentions=discord.AllowedMentions(users=True)
            )


# 📸 Reakcje bota — tylko na jednym kanale
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # ZAWSZE przepuszczaj komendy (!cwel, !ranking itd.)
    await bot.process_commands(message)

    content = message.content.lower().strip()

    # --- SMAKI (tylko w CWEL_CHANNEL_ID) ---
    if message.channel.id == CWEL_CHANNEL_ID and content == "smaki":
        procent = random.randint(0, 100)
        await message.channel.send(
            f"Dzisiaj procent smaczków na tytany wynosi: {procent}% 🍬"
        )
        return

    # Reaguj tylko w BOT_CHANNEL_ID
    if message.channel.id != BOT_CHANNEL_ID:
        return

    # --- IGOR ---
    if content == "igor":
        image_path = "igor.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🖼️ Nie znaleziono pliku igor.gif!")

    # --- CRY ---
    elif content == "cry":
        image_path = "cry.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("😢 Nie znaleziono pliku cry.gif!")

    # --- ROLAS ---
    elif content == "rolas":
        image_path = "rolas.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🐽 Nie znaleziono pliku rolas.gif!")

    # --- SMACZKI ---
    elif content == "smaczki":
        image_path = "smaczki.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🦴 Nie znaleziono pliku smaczki.gif!")

    # --- LUTS ---
    elif content == "cpun":
        target = await bot.fetch_user(393531629731315722)
        await message.channel.send(
            f"{target.mention}, zostałeś nazwany ćpunem przez swojego Pana 💀",
            allowed_mentions=discord.AllowedMentions(users=True)
        )

    # --- HANWAN ---
    elif content in ["do szkoly gowniarzu", "do szkoły gówniarzu"]:
        target = await bot.fetch_user(714341935363391532)
        await message.channel.send(
            f"{target.mention}, zostałeś wygoniony do szkółki przez swojego Pana 👑",
            allowed_mentions=discord.AllowedMentions(users=True)
        )

    # --- KRZEŁO ---
    elif any(user.id == 1384921756313063426 for user in message.mentions):
        await message.channel.send("WRUUUM na dwóch kółkach do roboty, dzisiaj tylko 16h🧑‍🦽‍➡️🧑‍🦽‍➡️🧑‍🦽‍➡️")

    # --- DZIM ---
    elif content == "dzim":
        image_path = "dzim.png"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
            await message.channel.send("Trzymam ich chłopaki!! 🤓")
        else:
            await message.channel.send("🖼️ Nie znaleziono pliku dzim.png!")

    # --- KRZYS ---
    elif content == "krzys":
        image_path = "krzys.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("😢 Nie znaleziono pliku krzys.gif!")

    # --- ZELWES ---
    elif any(user.id == 346327527909883914 for user in message.mentions):
        await message.channel.send("Hej kolego, masz błędny nick! Twój poprawny nick to **Cwelwes** 🤓")


# --- URUCHAMIANIE BOTA ---
token = os.getenv("TOKEN")
if not token:
    raise RuntimeError("❌ Brak zmiennej środowiskowej TOKEN!")

try:
    bot.run(token)
finally:
    if db_pool is not None:
        pass
