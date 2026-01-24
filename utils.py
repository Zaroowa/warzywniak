import datetime
import pytz
import os
import discord

TZ = pytz.timezone("Europe/Warsaw")

def get_now():
    return datetime.datetime.now(TZ)

async def send_image(channel, text, image_path=None, mention=None):
    if image_path and os.path.exists(image_path):
        await channel.send(
            text,
            file=discord.File(image_path),
            allowed_mentions=discord.AllowedMentions(users=True)
        )
    else:
        await channel.send(
            text,
            allowed_mentions=discord.AllowedMentions(users=True)
        )
