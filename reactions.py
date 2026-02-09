import os
import discord

async def handle_reactions(bot, message):
    content = message.content.lower().strip()

    # --- IGOR ---
    if content == "igor":
        image_path = "igor.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🖼️ Nie znaleziono pliku igor.gif!")
            
    # --- BUŁKASZ ---
    elif content == ["nie pytaj co się działo o 6 rano w piątek", "nie pytaj co sie dzialo o 6 rano w piatek"]:
        image_path = "hanwan.png"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🖼️ Nie znaleziono pliku hanwan.png!")
            
    # --- CRY ---
    elif content == "cry":
        image_path = "cry.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("😢 Nie znaleziono pliku cry.gif!")

    # --- ROLAS ---
    elif content == "rolas":
        image_path = "rolas.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🐽 Nie znaleziono pliku rolas.gif!")

    # --- SMACZKI ---
    elif content == "smaczki":
        image_path = "smaczki.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("🦴 Nie znaleziono pliku smaczki.gif!")

    # --- HANWAN ---
    elif content in ["do szkoly gowniarzu", "do szkoły gówniarzu"]:
        target = await bot.fetch_user(714341935363391532)
        await message.channel.send(
            f"{target.mention}, zostałeś wygoniony do szkółki przez swojego Pana 👑",
            allowed_mentions=discord.AllowedMentions(users=True)
        )

    # --- DZIM ---
    elif content == "dzim":
        image_path = "dzim.png"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
            await message.channel.send("Trzymam ich chłopaki!! 🤓")
        else:
            await message.channel.send("🖼️ Nie znaleziono pliku dzim.png!")

    # --- KRZYS ---
    elif content == "krzys":
        image_path = "krzys.gif"
        if os.path.exists(image_path):
            await message.channel.send(file=discord.File(image_path))
        else:
            await message.channel.send("😢 Nie znaleziono pliku krzys.gif!")
