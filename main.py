from keep_alive import keep_alive

keep_alive()

import discord
from discord.ext import commands, tasks
import random
import datetime
import asyncio
import os

# ---- KONFIGURACJA ----
GODZINA = 17  # godzina, o której bot ma pingować (24h format)
MINUTA = 5  # minuta
CHANNEL_ID = 1303471531560796180  # ID kanału, gdzie ma wysyłać wiadomość
# -----------------------

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    planowany_ping.start()

@tasks.loop(hours=24)
async def planowany_ping():
    now = datetime.datetime.now()
    target = now.replace(hour=GODZINA, minute=MINUTA, second=0, microsecond=0)

    if now >= target:
        target += datetime.timedelta(days=1)

    delay = (target - now).total_seconds()
    print(f"Oczekiwanie {delay} sekund do następnego pingnięcia...")
    await asyncio.sleep(delay)

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Nie znaleziono kanału.")
        return

    guild = channel.guild
    members = [member for member in guild.members if not member.bot]
    if not members:
        await channel.send("Brak użytkowników do pingnięcia.")
        return

    losowy = random.choice(members)
    await channel.send(f"{losowy.mention}, zostałeś wybrany na cwela dnia!")

@bot.command()
@commands.has_permissions(administrator=True)
async def cwel(ctx):
    guild = ctx.guild
    members = [member for member in guild.members if not member.bot]
    if not members:
        await ctx.send("Brak użytkowników do pingnięcia.")
        return

    losowy = random.choice(members)
    await ctx.send(f"{losowy.mention}, zostałeś wybrany na cwela dnia!")

print("TOKEN z os.getenv:", os.getenv("TOKEN"))
bot.run(os.getenv("TOKEN"))
