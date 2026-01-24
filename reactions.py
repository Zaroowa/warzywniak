# reactions.py
import os
import discord

async def handle_reactions(bot, message):
    content = message.content.lower().strip()

    gifs = {
        "igor": "igor.gif",
        "cry": "cry.gif",
        "rolas": "rolas.gif",
        "smaczki": "smaczki.gif",
        "krzys": "krzys.gif"
    }

    if content in gifs:
        path = gifs[content]
        if os.path.exists(path):
            await message.channel.send(file=discord.File(path))
        return
