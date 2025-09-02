from keep_alive import keep_alive
keep_alive()

import discord
from discord.ext import commands, tasks
import random
import datetime
import asyncio
import os
import pytz
import json
import asyncpg

# ---- KONFIGURACJA ----
GODZINA = 16  # godzina pingowania (24h)
MINUTA = 0    # minuta pingowania
CHANNEL_ID = 1303471531560796180
RANKING_FILE = "ranking.json"
ALLOWED_USERS = [630387902211162122, 388975847396081675]  # <<< wpisz swoje ID albo listę ID
# -----------------------

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Inicjalizacja rankingu
if not os.path.exists(RANKING_FILE):
    with open(RANKING_FILE, "w") as f:
        json.dump({}, f)

def load_ranking():
    with open(RANKING_FILE, "r") as f:
        return json.load(f)

def save_ranking(ranking):
    with open(RANKING_FILE, "w") as f:
        json.dump(ranking, f, indent=2)

last_pinged_user_id = None

@bot.event
async def on_ready():
    await connect_db()
    print(f"✅ Zalogowano jako {bot.user}")
    planowany_ping.start()

# 🔄 Sprawdzanie co minutę
@tasks.loop(minutes=1)
async def planowany_ping():
    global last_pinged_user_id

    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.datetime.now(tz)

    # sprawdzamy czy jest ustawiona godzina i minuta
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

        ranking = load_ranking()
        ranking[str(losowy.id)] = ranking.get(str(losowy.id), 0) + 1
        save_ranking(ranking)

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

    ranking = load_ranking()
    ranking[str(losowy.id)] = ranking.get(str(losowy.id), 0) + 1
    save_ranking(ranking)

    await ctx.send(f"{losowy.mention}, zostałeś wybrany na cwela dnia! 💀")

# 📊 Ranking
@bot.command()
async def ranking(ctx):
    ranking = load_ranking()
    if not ranking:
        await ctx.send("Brak danych w rankingu.")
        return

    sorted_ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    lines = []
    for i, (user_id, count) in enumerate(sorted_ranking[:10], 1):
        user = await bot.fetch_user(int(user_id))
        lines.append(f"{i}. {user.name}#{user.discriminator} - {count} razy")

    await ctx.send("🏆 Ranking cweli dnia:\n" + "\n".join(lines))

DB_URL = os.getenv("DATABASE_URL")
db_pool = None

async def connect_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DB_URL)

# --- URUCHAMIANIE BOTA ---
token = os.getenv("TOKEN")
if not token:
    raise RuntimeError("❌ Brak zmiennej środowiskowej TOKEN!")

bot.run(token)
