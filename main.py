from keep_alive import keep_alive
keep_alive()

import discord
from discord.ext import commands
from scheduler import scheduler
from db import connect_db, init_db
from reactions import handle_reactions
import commands as cmd

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await connect_db()
    await init_db()
    scheduler.start(bot)
    print(f"✅ Zalogowano jako {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await handle_reactions(bot, message)
    await bot.process_commands(message)

cmd.setup(bot)
bot.run(os.getenv("TOKEN"))
