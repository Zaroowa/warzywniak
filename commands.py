print("📦 commands.py ZAŁADOWANY")

import random
from discord.ext import commands
from db import update_ranking, load_top_n
from scheduler import get_tasks, find_task, run_task

# ---------------------- KONFIGURACJA ----------------------
ALLOWED_ROLE_NAMES = ["Rada", "Fuhrer"]
ALLOWED_USER_IDS = [388975847396081675]
CWEL_CHANNEL_ID = 1303471531560796180
SMAKI_CHANNEL_ID = 1325976696788353165
SPECIAL_USER_ID = 393531629731315722

# ---------------------- KOMENDY ----------------------

@bot.command()
async def cwel(ctx):
    if ctx.channel.id != CWEL_CHANNEL_ID:
        return

    if ctx.author.id not in ALLOWED_USERS:
        await ctx.send("Ty nie losujesz cwela — **TY JESTEŚ CWELEM NAD CWELE!** 💀🔥")
        return

    # 🟡 SPECJALNY PRZYPADEK
    if ctx.author.id == SPECIAL_USER_ID:
        await ctx.send(f"<@{393531629731315722}>, zostałeś wybrany na cwela dnia! 💀" )
        return

    # 🔴 NORMALNE LOSOWANIE
    guild = ctx.guild
    members = [m for m in guild.members if not m.bot]
    if not members:
        await ctx.send("Brak użytkowników do pingnięcia.")
        return

    losowy = random.choice(members)

    if db_pool:
        await update_ranking(losowy.id)

    await ctx.send(f"{losowy.mention}, zostałeś wybrany na cwela dnia! 💀")

# --- !SMAKI ---
@commands.cooldown(1, 3600, commands.BucketType.user)
async def smaki(ctx):
    # --- sprawdzenie kanału ---
    if ctx.channel.id != SMAKI_CHANNEL_ID:
        await ctx.send(f"❌ Komenda `!smaki` działa tylko na tym kanale: <#{SMAKI_CHANNEL_ID}>")
        return

    # --- osoby uprzywilejowane ---
    has_role = any(role.name in ALLOWED_ROLE_NAMES for role in ctx.author.roles)
    has_user = ctx.author.id in ALLOWED_USER_IDS

    # uprzywilejowani nie mają cooldownu
    if has_role or has_user:
        ctx.command.reset_cooldown(ctx)

    procent = random.randint(0, 100)
    await ctx.send(f"Dzisiaj procent smaczków: {procent}% 🍬")

# --- !RANKING ---
async def ranking(ctx):
    top = await load_top_n(10)
    msg = "🏆 **Ranking:**\n"

    for i, (uid, count) in enumerate(top, 1):
        user = await ctx.bot.fetch_user(uid)
        msg += f"{i}. {user.name} — {count}\n"

    await ctx.send(msg)

# --- !TASKS ---
async def tasks(ctx, action=None, task_name=None):
    has_role = any(role.name in ALLOWED_ROLE_NAMES for role in ctx.author.roles)
    has_user = ctx.author.id in ALLOWED_USER_IDS

    if not has_role and not has_user:
        await ctx.send("❌ Nie masz uprawnień do używania tej komendy!")
        return

    tasks_list = get_tasks()

    if action is None:
        lines = ["📋 **Taski:**"]
        for t in tasks_list:
            status = "🟢" if t["enabled"] else "🔴"
            days = "dni robocze" if t["weekdays"] else "codziennie"
            lines.append(
                f"{status} `{t['name']}` — {t['hour']:02d}:{t['minute']:02d} ({days})"
            )
        await ctx.send("\n".join(lines))
        return

    if action in ("on", "off") and task_name:
        task = find_task(task_name)
        if not task:
            await ctx.send("❌ Nie znaleziono takiego taska")
            return

        task["enabled"] = action == "on"
        await ctx.send(
            f"✅ Task `{task_name}` {'włączony' if task['enabled'] else 'wyłączony'}"
        )
        return

    if action == "run" and task_name:
        ok, msg = await run_task(ctx.bot, task_name)
        await ctx.send(("✅ " if ok else "❌ ") + msg)
        return

    await ctx.send("❓ Użycie: `!tasks`, `!tasks on/off <nazwa>`, `!tasks run <nazwa>`")

# ---------------------- REJESTRACJA ----------------------
def setup(bot):
    bot.add_command(commands.Command(cwel))
    bot.add_command(commands.Command(smaki))
    bot.add_command(commands.Command(ranking))
    bot.add_command(commands.Command(tasks))
    print("🧩 setup(bot) URUCHOMIONY")
