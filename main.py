import discord
from discord.ext import commands, tasks
import random
import datetime
import asyncio
import pytz
import os

# ---- KONFIGURACJA ----
GODZINA = 16
MINUTA = 00
CHANNEL_ID = 1303471531560796180  # Twój kanał
# -----------------------

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

local_tz = pytz.timezone("Europe/Warsaw")


@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    planowany_ping.start()


@tasks.loop(hours=24)
async def planowany_ping():
    now = datetime.datetime.now(local_tz)
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

    await pingnij_losowego(channel)


# --- NOWA KOMENDA !cwel ---
@bot.command(name="cwel")
@commands.has_permissions(administrator=True)
async def cwel(ctx):
    await pingnij_losowego(ctx.channel)


# --- FUNKCJA DO PINGOWANIA LOSOWEJ OSOBY ---
async def pingnij_losowego(channel):
    guild = channel.guild
    members = [member for member in guild.members if not member.bot]
    if not members:
        await channel.send("Brak użytkowników do pingnięcia.")
        return

    losowy = random.choice(members)
    await channel.send(f"{losowy.mention}, zostałeś wybrany na cwela dnia!")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Nie masz uprawnień do użycia tej komendy.")
    else:
        raise error


bot.run(os.getenv("TOKEN"))
