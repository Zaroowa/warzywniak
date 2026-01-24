from discord.ext import tasks
from utils import get_now, send_image
from dyktanda import DYKTANDA
from db import update_ranking
import random
import os

LAST_RUN = {}
TASKS = []

BOT_CHANNEL_ID = 1325976696788353165
KRZELO_ID = 1384921756313063426
DYKTANDO_USER_ID = 807664458058825729
DYKTANDO_CHANNEL_ID = 1325976696788353165
DYKTANDO_HOUR = 17
DYKTANDO_MINUTE = 45

# ---- TASK HELPER ----
def get_tasks():
    return TASKS

def find_task(name):
    for t in TASKS:
        if t["name"] == name:
            return t
    return None

def task(name, hour, minute, weekdays=False):
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

async def run_task(bot, name):
    task_obj = find_task(name)
    if not task_obj:
        return False, "Nie znaleziono taska"
    await task_obj["func"](bot)
    return True, f"Task `{name}` uruchomiony ręcznie"

# ---- SCHEDULER LOOP ----
@tasks.loop(minutes=1)
async def scheduler(bot):
    now = get_now()
    for t in TASKS:
        if not t["enabled"]:
            continue
        if now.hour != t["hour"] or now.minute != t["minute"]:
            continue
        if t["weekdays"] and now.weekday() >= 5:
            continue
        key = (t["name"], now.date())
        if LAST_RUN.get(key):
            continue
        await t["func"](bot)
        LAST_RUN[key] = True

# ---- TASKS ----
@task("krzelo_morning", 4, 0, weekdays=True)
async def krzelo_morning(bot):
    channel = bot.get_channel(BOT_CHANNEL_ID)
    user = await bot.fetch_user(KRZELO_ID)
    await send_image(
        channel,
        f"{user.mention} Wstawaj Krzeło! Dzisiaj tylko 16h do odjebania za najniższą krajową! 🧑‍🦽‍➡️",
        "adios.png"
    )

@task("krzelo_evening", 20, 0, weekdays=True)
async def krzelo_evening(bot):
    channel = bot.get_channel(BOT_CHANNEL_ID)
    user = await bot.fetch_user(KRZELO_ID)
    await send_image(
        channel,
        f"{user.mention} Gratulacje! Właśnie odjebałeś podwójną zmianę jak typowy ukr! 🧑‍🦽‍➡️",
        "krzeloo.png"
    )

@task("dyktando", DYKTANDO_HOUR, DYKTANDO_MINUTE)
async def dyktando_task(bot):
    channel = bot.get_channel(DYKTANDO_CHANNEL_ID)
    if not channel:
        print("❌ Nie znaleziono kanału do dyktanda")
        return
    user = await bot.fetch_user(DYKTANDO_USER_ID)
    tekst = random.choice(DYKTANDA)
    await channel.send(
        f"{user.mention}\n{tekst}",
        allowed_mentions=discord.AllowedMentions(users=True)
    )

@task("test_all", 0, 0)  # godzina/minuta są ignorowane, wywołasz ręcznie
async def test_all(bot):
    channel = bot.get_channel(BOT_CHANNEL_ID)
    
    # 1️⃣ Ping poranny
    user = await bot.fetch_user(KRZELO_ID)
    await send_image(channel, f"{user.mention} Wstawaj Krzeło! 🧑‍🦽‍➡️", "adios.png")
    
    # 2️⃣ Ping wieczorny
    await send_image(channel, f"{user.mention} Gratulacje! 🧑‍🦽‍➡️", "krzeloo.png")
    
    # 3️⃣ Dyktando
    dyktando_user = await bot.fetch_user(DYKTANDO_USER_ID)
    tekst = random.choice(DYKTANDA)
    await channel.send(f"{dyktando_user.mention}\n{tekst}")
    
    # 4️⃣ Test reakcji z obrazkami
    for img in ["igor.gif", "cry.gif", "rolas.gif", "smaczki.gif", "dzim.png", "krzys.gif"]:
        if os.path.exists(img):
            await channel.send(file=discord.File(img))
