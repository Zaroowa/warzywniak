from scheduler import get_tasks, find_task, run_task
from db import load_top_n
import random
from discord.ext import commands

def setup(bot):

    @bot.command()
    async def smaki(ctx):
        if ctx.channel.id != 1325976696788353165:  # BOT_CHANNEL_ID
            return
        procent = random.randint(0, 100)
        await ctx.send(f"Dzisiaj procent smaków: {procent}% 🍬")

    @bot.command()
    async def ranking(ctx):
        top = await load_top_n(10)
        msg = "🏆 Ranking:\n"
        for i, (uid, count) in enumerate(top, 1):
            user = await bot.fetch_user(uid)
            msg += f"{i}. {user.name} - {count}\n"
        await ctx.send(msg)

    @bot.command()
    async def tasks(ctx, action=None, task_name=None):
        tasks_list = get_tasks()

        # ---- OGRANICZENIE DOSTĘPU ----
        ALLOWED_ROLE_NAMES = ["Rada", "Fuhrer"]        # nazwa roli, która może używać !tasks
        ALLOWED_USER_ID = 388975847396081675  # ID użytkownika, który może używać !tasks

        has_role = any(role.name in ALLOWED_ROLE_NAMES for role in ctx.author.roles)
        if not has_role and ctx.author.id != ALLOWED_USER_ID:
            await ctx.send("❌ Nie masz uprawnień do używania tej komendy!")
            return
        # -------------------------------------

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

        # !tasks on/off
        if action in ("off", "on") and task_name:
            task_obj = find_task(task_name)
            if not task_obj:
                await ctx.send("❌ Nie znaleziono takiego taska")
                return
            task_obj["enabled"] = action == "on"
            await ctx.send(
                f"✅ Task `{task_name}` {'włączony' if task_obj['enabled'] else 'wyłączony'}"
            )
            return

        # !tasks run
        if action == "run" and task_name:
            ok, msg = await run_task(ctx.bot, task_name)
            await ctx.send("✅ " + msg if ok else "❌ " + msg)
            return

        await ctx.send("❓ Użycie: `!tasks`, `!tasks on/off <nazwa>`, `!tasks run <nazwa>`")
