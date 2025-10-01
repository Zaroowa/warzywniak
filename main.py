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
CHANNEL_ID = 1303471531560796180
ALLOWED_USERS = [630387902211162122, 388975847396081675, 304303798766010369]  # <<< wpisz swoje ID albo listę ID
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
    # utworzenie tabeli jeśli nie istnieje
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
        # wstaw lub inkrementuj
        await conn.execute("""
        INSERT INTO ranking (user_id, count)
        VALUES ($1, 1)
        ON CONFLICT (user_id)
        DO UPDATE SET count = ranking.count + 1
        """, user_id)

async def load_ranking_dict():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id, count FROM ranking")
        return {str(r['user_id']): r['count'] for r in rows}

async def load_top_n(n=10):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id, count FROM ranking ORDER BY count DESC LIMIT $1", n)
        return [(r['user_id'], r['count']) for r in rows]

# --- Events / Tasks ---
@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")
    # Połącz do DB i inicjalizuj tabelę
    if DB_URL:
        await connect_db()
        await init_db()
    else:
        print("⚠️ DATABASE_URL nie ustawione — bot będzie działać bez DB (brak zapisu rankingu).")
    planowany_ping.start()

# 🔄 Sprawdzanie co minutę
@tasks.loop(minutes=1)
async def planowany_ping():
    global last_pinged_user_id

    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.datetime.now(tz)

    if now.hour == GODZINA and now.minute == MINUTA:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            print("❌ Nie znaleziono kanału.")
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
        else:
            print("⚠️ DB niedostępna — nie zapisano do rankingu.")

        await channel.send(f"{losowy.mention}, zostałeś wybrany na cwela dnia! 💀")

# 🔒 Komenda z uprawnieniami na ID
@bot.command()
async def cwel(ctx):
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
        await ctx.send("Ranking niedostępny — baza danych niepodłączona.")
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
# 📸 Reakcja na słowo
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return  # ignoruj wiadomości od botów

    content = message.content.lower().strip()

    # --- IGOR ---
    if content == "igor":
        image_path = "igor.gif"  # ścieżka do obrazka igor.gif
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🖼️ Nie znaleziono pliku igor.gif!")

    # --- CRY ---
    elif content == "cry":
        image_path = "cry.gif"  # ścieżka do obrazka cry.gif
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("😢 Nie znaleziono pliku cry.gif!")

     # --- ROLAS ---
    elif content == "rolas":
        image_path = "rolas.gif"  # ścieżka do obrazka rolas.gif
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🐽 Nie znaleziono pliku rolas.gif!")

      # --- SMACZKI ---
    elif content == "smaczki":
        image_path = "smaczki.gif"  # ścieżka do obrazka smaczki.gif
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🦴 Nie znaleziono pliku smaczki.gif!")

    # --- ZJEB ---
elif content.startswith("zjeb"):
    # sprawdź, czy ktoś został wspomniany w wiadomości
    if message.mentions:
        target = message.mentions[0]
        await message.channel.send(
            f"{target.mention}, zostałeś nazwany zjebem przez {message.author.mention} 💀",
            allowed_mentions=discord.AllowedMentions(users=True)
        )
    else:
        await message.channel.send("@luts5708")
            
    # przepuszczanie wiadomości do innych komend (!ranking itd.)
    await bot.process_commands(message)
    print(os.listdir("."))  # wypisze pliki w katalogu bota
# --- URUCHAMIANIE BOTA ---
token = os.getenv("TOKEN")
if not token:
    raise RuntimeError("❌ Brak zmiennej środowiskowej TOKEN!")

try:
    bot.run(token)
finally:
    # przy zamykaniu aplikacji możesz dodatkowo zamknąć pool (Railway to zrestartuje i tak)
    if db_pool is not None:
        # Nie możemy awaitować tu (outside async), ale pool zostanie czyszczony przy proces exit.
        pass
