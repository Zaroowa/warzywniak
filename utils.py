import datetime
import os
import pytz
import discord

def get_now():
    tz_name = os.getenv("TZ", "Europe/Warsaw")
    tz = pytz.timezone(tz_name)
    return datetime.datetime.now(tz)

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
