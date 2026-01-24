# commands.py
from discord.ext import commands
from db import update_ranking, load_top_n
import random

def setup(bot):

    @bot.command()
    async def smaki(ctx):
        procent = random.randint(0, 100)
        await ctx.send(f"Dzisiaj procent smaczków: {procent}% 🍬")

    @bot.command()
    async def ranking(ctx):
        top = await load_top_n(10)
        msg = "🏆 Ranking:\n"
        for i, (uid, count) in enumerate(top, 1):
            user = await bot.fetch_user(uid)
            msg += f"{i}. {user.name} - {count}\n"
        await ctx.send(msg)
