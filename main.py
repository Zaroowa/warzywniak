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

# ---- KONFIGURACJA ----
GODZINA = 17  # godzina pingowania (24h)
MINUTA = 15   # minuta pingowania
CHANNEL_ID = 1303471531560796180
RANKING_FILE = "ranking.json"
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
    print(f"✅ Zalogowano jako {bot.user}")
    planowany_ping.start()

@tasks.loop(hours=24)
async def planowany_ping():
    global last_pinged_user_id

    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.datetime.now(tz)
    target = now.replace(hour=GODZINA, minute=MINUTA, second=0, microsecond=0)
    if now >= target:
        target += datetime.timedelta(days=1)

    delay = (target - now).total_seconds()
    print(f"🕒 Aktualny czas: {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    print(f"📅 Pingowanie zaplanowane na: {target.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    print(f"⏳ Oczekiwanie {int(delay)} sekund do następnego pingnięcia...\n")
    await asyncio.sleep(delay)

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

@bot.command()
@commands.has_permissions(administrator=True)
async def cwel(ctx):
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

# --- URUCHAMIANIE BOTA ---
token = os.getenv("TOKEN")
if not token:
    raise RuntimeError("❌ Brak zmiennej środowiskowej TOKEN!")

bot.run(token)
