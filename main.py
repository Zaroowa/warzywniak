from keep_alive import keep_alive
keep_alive()

import os
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
    await bot.wait_until_ready()
    await connect_db()
    await init_db()

    if not scheduler.is_running():
        scheduler.start(bot)

    print(f"✅ Zalogowano jako {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await handle_reactions(bot, message)
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes = int(error.retry_after // 60)
        seconds = int(error.retry_after % 60)
        await ctx.send(
            f"⏳ Spokojnie! `!smaki` będzie dostępne za **{minutes}m {seconds}s**."
        )
        return

    raise error

cmd.setup(bot)
bot.run(os.getenv("TOKEN"))
