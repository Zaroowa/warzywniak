@bot.event
async def on_ready():
    await connect_db()
    print(f"✅ Zalogowano jako {bot.user}")
    planowany_ping.start()
