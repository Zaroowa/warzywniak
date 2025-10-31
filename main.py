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
ALLOWED_USERS = [630387902211162122, 388975847396081675, 304303798766010369, 495334844088451083, 1253834602724982785, 714341935363391532, 703166818847555605, 319810513536286720]  # <<< wpisz swoje ID albo listę ID
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
    krzelo_ping.start()

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

# 🔒 Uprawnienia do !cwel
@bot.command()
async def cwel(ctx):
    if ctx.channel.id != CWEL_CHANNEL_ID:
        return  # komenda !cwel działa tylko w jednym kanale
        
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

# 🔔 Ping o 4:00 w dni robocze
@tasks.loop(minutes=1)
async def krzelo_ping():
    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.datetime.now(tz)

    # Dni tygodnia: poniedziałek = 0, niedziela = 6
    if now.weekday() < 5 and now.hour == 4 and now.minute == 0:
        channel = bot.get_channel(BOT_CHANNEL_ID)
        if channel is None:
            print("❌ Nie znaleziono kanału dla krzelo_ping.")
            return

        target_id = 1384921756313063426  # 🔁 podmień na ID krzeła
        target = await bot.fetch_user(target_id)

        image_path = "adios.png"  # obrazek z folderu bota
        if os.path.exists(image_path):
            await channel.send(
                f"{target.mention} Wstawaj Krzeło! Dzisiaj tylko 16h do odjebania za najniższą krajową! 🧑‍🦽‍➡️",
                file=discord.File(image_path),
                allowed_mentions=discord.AllowedMentions(users=True)
            )
        else:
            await channel.send(
                f"{target.mention} Wstawaj Krzeło! Dzisiaj tylko 16h do odjebania za najniższą krajową! 🧑‍🦽‍➡️ (brak obrazka)",
                allowed_mentions=discord.AllowedMentions(users=True)
            )
            
# 📸 Reakcja na słowo
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return  # ignoruj wiadomości od botów

    # reaguj tylko na jednym kanale
    if message.channel.id != BOT_CHANNEL_ID:
        return

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

     # --- LUTS ---
    elif content == "cpun":
        # ID użytkownika, którego bot ma pingować
        target_id = 393531629731315722  # ← zmień na właściwe ID
        target = await bot.fetch_user(target_id)
        await message.channel.send(
            f"{target.mention}, zostałeś nazwany ćpunem przez swojego Pana 💀",
            allowed_mentions=discord.AllowedMentions(users=True)
        )
        
     # --- HANWAN ---
    elif content == "do szkoly gowniarzu" or content == "do szkoły gówniarzu":
        # ID użytkownika, którego bot ma pingować
        target_id = 714341935363391532  # ← zmień na właściwe ID
        target = await bot.fetch_user(target_id)
        await message.channel.send(
            f"{target.mention}, zostałeś wygoniony do szkółki przez swojego Pana 👑",
            allowed_mentions=discord.AllowedMentions(users=True)
        )

    # --- KRZEŁO ---
        # 🧑‍🦽‍➡️ reakcja na ping konkretnej osoby
        # ID osoby, której ping ma wywoływać reakcję bota
    monitored_id = 1384921756313063426  # ← wpisz tutaj ID osoby, której ping ma aktywować emotkę

    if any(user.id == monitored_id for user in message.mentions):
        await message.channel.send("WRUUUM na dwóch kółkach do roboty, dzisiaj tylko 16h🧑‍🦽‍➡️🧑‍🦽‍➡️🧑‍🦽‍➡️")

    # --- DZIM ---
    if content == "dzim":
        image_path = "dzim.png"  # ścieżka do obrazka dzim.png
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
            await message.channel.send("Trzymam ich chłopaki!! 🤓")  # ← tekst po obrazku
        else:
            await message.channel.send("🖼️ Nie znaleziono pliku dzim.png!")

    # --- KRZYS ---
    elif content == "krzys":
        image_path = "krzys.gif"  # ścieżka do obrazka krzys.gif
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("😢 Nie znaleziono pliku krzys.gif!")
            
    # --- ZELWES ---
        # 🧑‍🦽‍➡️ reakcja na ping konkretnej osoby
        # ID osoby, której ping ma wywoływać reakcję bota
    monitored_id = 346327527909883914  # ← wpisz tutaj ID osoby, której ping ma aktywować emotkę

    if any(user.id == monitored_id for user in message.mentions):
        await message.channel.send("Hej kolego, masz błędny nick! Twój poprawny nick to **Cwelwes** 🤓")

    # --- KUBAKSI ---
    elif any(mention.id == 816391222960062464 for mention in message.mentions):
        procent = random.randint(0, 100)
        await message.channel.send(
            f"Dzisiaj procent smaczków na kica wynosi: {procent}% 🍪🐇"
        )

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
