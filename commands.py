print("📦 commands.py ZAŁADOWANY")

import random
from discord.ext import commands
from db import update_ranking, load_top_n
from scheduler import get_tasks, find_task, run_task

# ---------------------- KONFIG ----------------------
ALLOWED_ROLE_NAMES = ["Rada", "Fuhrer"]
ALLOWED_USER_IDS = [388975847396081675]
CWEL_CHANNEL_ID = 1303471531560796180
# ---------------------------------------------------


def has_permission(ctx):
    if ctx.author.id in ALLOWED_USER_IDS:
        return True
    return any(role.name in ALLOWED_ROLE_NAMES for role in ctx.author.roles)


def setup(bot):
    print("🧩 setup(bot) URUCHOMIONY")

    # ---------- !CWEL ----------
    @bot.command()
    async def cwel(ctx):
        if ctx.channel.id != CWEL_CHANNEL_ID:
            await ctx.send(f"❌ `!cwel` działa tylko tutaj: <#{CWEL_CHANNEL_ID}>")
            return

        if not has_permission(ctx):
            await ctx.send("❌ Nie masz uprawnień do tej komendy!")
            return

        members = [m for m in ctx.guild.members if not m.bot]
        user = random.choice(members)

        await update_ranking(user.id)
        await ctx.send(f"{user.mention}, zostałeś wybrany na **cwela dnia** 💀")

    # ---------- !SMAKI (cooldown 1h) ----------
    @bot.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def smaki(ctx):
        procent = random.randint(0, 100)
        await ctx.send(f"Dzisiaj procent smaczków: **{procent}%** 🍬")

    # ---------- !RANKING ----------
    @bot.command()
    async def ranking(ctx):
        top = await load_top_n(10)
        msg = "🏆 **Ranking:**\n"
        for i, (uid, count) in enumerate(top, 1):
            user = await bot.fetch_user(uid)
            msg += f"{i}. {user.name} — {count}\n"
        await ctx.send(msg)

    # ---------- !TASKS ----------
    @bot.command()
    async def tasks(ctx, action=None, task_name=None):
        if not has_permission(ctx):
            await ctx.send("❌ Nie masz uprawnień do tej komendy!")
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
                await ctx.send("❌ Nie znaleziono taska")
                return

            task["enabled"] = action == "on"
            await ctx.send(
                f"✅ Task `{task_name}` {'włączony' if task['enabled'] else 'wyłączony'}"
            )
            return

        if action == "run" and task_name:
            ok, msg = await run_task(ctx.bot, task_name)
            await ctx.send("✅ " + msg if ok else "❌ " + msg)
            return

        await ctx.send("❓ Użycie: `!tasks`, `!tasks on/off <nazwa>`, `!tasks run <nazwa>`")
