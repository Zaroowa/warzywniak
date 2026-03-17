import discord
import random
from discord.ext import tasks

from utils import get_now, send_image
from dyktanda import DYKTANDA
from db import update_ranking

# --------------------------------------
# ZMIENNE GLOBALNE
# --------------------------------------
LAST_RUN = {}
TASKS = []

BOT_CHANNEL_ID = 1325976696788353165
KRZELO_ID = 1384921756313063426
CWEL_CHANNEL_ID = 1303471531560796180

# --------------------------------------
# FUNKCJE POMOCNICZE
# --------------------------------------
def get_tasks():
    return TASKS

def find_task(name):
    for t in TASKS:
        if t["name"] == name:
            return t
    return None

def task(name, hour, minute, weekdays=False):
    """Dekorator do tworzenia tasków"""
    def decorator(func):
        TASKS.append({
            "name": name,
            "hour": hour,
            "minute": minute,
            "weekdays": weekdays,
            "func": func,
            "enabled": True
        })
        return func
    return decorator

# --------------------------------------
# GŁÓWNY SCHEDULER
# --------------------------------------
@tasks.loop(minutes=1)
async def scheduler(bot):
    now = get_now()
    print("🕒 scheduler tick:", now.strftime("%Y-%m-%d %H:%M"))

    for t in TASKS:
        if not t["enabled"]:
            continue

        if t["weekdays"] and now.weekday() >= 5:
            continue

        if not (
            now.hour == t["hour"]
            and t["minute"] <= now.minute <= t["minute"] + 1
        ):
            continue

        key = (t["name"], now.date())
        if LAST_RUN.get(key):
            continue

        print(f"▶️ URUCHAMIAM TASK: {t['name']}")
        await t["func"](bot)
        LAST_RUN[key] = True

# --------------------------------------
# TASKI
# --------------------------------------

# 🔔 Krzeło rano — 4:00 (dni robocze)
@task("krzelo_morning", 4, 0, weekdays=True)
async def krzelo_morning(bot):
    channel = bot.get_channel(BOT_CHANNEL_ID)
    user = await bot.fetch_user(KRZELO_ID)

    await send_image(
        channel,
        f"{user.mention} Wstawaj Krzeło! Dzisiaj tylko 16h do odjebania za najniższą krajową! 🧑‍🦽‍➡️",
        "adios.png"
    )

# 🔔 Krzeło wieczorem — 20:00 (dni robocze)
@task("krzelo_evening", 20, 0, weekdays=True)
async def krzelo_evening(bot):
    channel = bot.get_channel(BOT_CHANNEL_ID)
    user = await bot.fetch_user(KRZELO_ID)

    await send_image(
        channel,
        f"{user.mention} Gratulacje! Właśnie odjebałeś podwójną zmianę jak typowy Ukr! 🧑‍🦽‍➡️",
        "krzeloo.png"
    )

# 🤡 Automatyczny !cwel — 16:00 codziennie
@task("cwel_automatyczne", 16, 0)
async def cwel_automatyczne(bot):
    channel = bot.get_channel(CWEL_CHANNEL_ID)
    if not channel:
        print("❌ Nie znaleziono kanału dla automatycznego !cwel")
        return

    members = [m for m in channel.guild.members if not m.bot]
    if not members:
        return

    user = random.choice(members)
    await update_ranking(user.id)
    await channel.send(f"{user.mention}, zostałeś wybrany na cwela dnia! 💀")

# ✍️ Dyktando — 18:00 codziennie
@task("dyktando", 18, 0)
async def dyktando(bot):
    channel = bot.get_channel(BOT_CHANNEL_ID)
    if not channel:
        print("❌ Nie znaleziono kanału dla dyktanda")
        return

    user = await bot.fetch_user(807664458058825729)
    tekst = random.choice(DYKTANDA)

    await channel.send(
        f"{user.mention}\n{tekst}",
        allowed_mentions=discord.AllowedMentions(users=True)
    )
# --------------------------------------
# RĘCZNE URUCHAMIANIE TASKA (!tasks run)
# --------------------------------------
async def run_task(bot, name):
    task = find_task(name)
    if not task:
        return False, "Nie znaleziono taska"

    await task["func"](bot)
    return True, f"Task `{name}` uruchomiony ręcznie"
