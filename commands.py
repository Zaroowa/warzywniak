import random
from discord.ext import commands
from db import update_ranking, load_top_n
from scheduler import get_tasks, find_task, run_task

# ---------------------- KONFIGURACJA ----------------------
ALLOWED_ROLE_NAMES = ["Rada", "Fuhrer"]
ALLOWED_USER_IDS = [388975847396081675]
CWEL_CHANNEL_ID = 1303471531560796180

# ---------------------- KOMENDY ----------------------

# --- !CWEL ---
async def cwel(ctx):
    # Sprawdzenie kanału
    if ctx.channel.id != CWEL_CHANNEL_ID:
        await ctx.send(f"❌ Komenda `!cwel` działa tylko na tym kanale: <#1303471531560796180>!")
        return

    # sprawdzenie uprawnień takie same jak w !tasks
    has_role = any(role.name in ALLOWED_ROLE_NAMES for role in ctx.author.roles)
    has_user = ctx.author.id in ALLOWED_USER_IDS
    if not has_role and not has_user:
        await ctx.send("❌ Nie masz uprawnień do używania tej komendy!")
        return

    members = [m for m in ctx.guild.members if not m.bot]
    user = random.choice(members)

    await update_ranking(user.id)
    await ctx.send(f"{user.mention}, zostałeś wybrany na cwela dnia! 💀")


# --- !SMAKI ---
@commands.cooldown(1, 3600, commands.BucketType.user)
async def smaki(ctx):
    procent = random.randint(0, 100)
    await ctx.send(f"Dzisiaj procent smaczków: {procent}% 🍬")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes = int(error.retry_after // 60)
        seconds = int(error.retry_after % 60)
        await ctx.send(
            f"⏳ Spokojnie! `!smaki` będzie dostępne za **{minutes}m {seconds}s**."
        )


# --- !RANKING ---
async def ranking(ctx):
    top = await load_top_n(10)
    msg = "🏆 Ranking:\n"
    for i, (uid, count) in enumerate(top, 1):
        user = await ctx.bot.fetch_user(uid)
        msg += f"{i}. {user.name} - {count}\n"
    await ctx.send(msg)


# --- !TASKS ---
async def tasks(ctx, action=None, task_name=None):
    # sprawdzenie uprawnień
    has_role = any(role.name in ALLOWED_ROLE_NAMES for role in ctx.author.roles)
    has_user = ctx.author.id in ALLOWED_USER_IDS
    if not has_role and not has_user:
        await ctx.send("❌ Nie masz uprawnień do używania tej komendy!")
        return

    tasks_list = get_tasks()

    # !tasks
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

    # !tasks on/off <name>
    if action in ("off", "on") and task_name:
        task = find_task(task_name)
        if not task:
            await ctx.send("❌ Nie znaleziono takiego taska")
            return

        task["enabled"] = action == "on"
        await ctx.send(
            f"✅ Task `{task_name}` {'włączony' if task['enabled'] else 'wyłączony'}"
        )
        return

    # !tasks run <name>
    if action == "run" and task_name:
        ok, msg = await run_task(ctx.bot, task_name)
        await ctx.send("✅ " + msg if ok else "❌ " + msg)
        return

    await ctx.send("❓ Użycie: `!tasks`, `!tasks on/off <nazwa>`, `!tasks run <nazwa>`")


# ---------------------- REJESTRACJA KOMEND ----------------------
def setup(bot):
    bot.add_command(commands.Command(cwel))
    bot.add_command(commands.Command(smaki))
    bot.add_command(commands.Command(ranking))
    bot.add_command(commands.Command(tasks))
