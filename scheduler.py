# scheduler.py
from discord.ext import tasks
from utils import get_now, send_image
import random
from dyktanda import DYKTANDA
from db import update_ranking

LAST_RUN = {}

TASKS = []

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

  BOT_CHANNEL_ID = 1325976696788353165
  KRZELO_ID = 1384921756313063426

@task("krzelo_morning", 4, 0, weekdays=True)
async def krzelo_morning(bot):
    channel = bot.get_channel(BOT_CHANNEL_ID)
    user = await bot.fetch_user(KRZELO_ID)
    await send_image(
        channel,
        f"{user.mention} Wstawaj Krzeło! 🧑‍🦽‍➡️",
        "adios.png"
    )

@task("krzelo_evening", 20, 0, weekdays=True)
async def krzelo_evening(bot):
    channel = bot.get_channel(BOT_CHANNEL_ID)
    user = await bot.fetch_user(KRZELO_ID)
    await send_image(
        channel,
        f"{user.mention} Gratulacje! 🧑‍🦽‍➡️",
        "krzeloo.png"
    )
