from scheduler import get_tasks, find_task, run_task
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

@bot.command()
async def tasks(ctx, action=None, task_name=None):
    tasks_list = get_tasks()

    # -------- OGRANICZENIE DOSTĘPU --------
ALLOWED_ROLES = ["Rada", "Fuhrer"]        # nazwa roli, która może używać !tasks
ALLOWED_USER_ID = 1464679842107621488  # ID użytkownika, który może używać !tasks

# sprawdzenie uprawnień
has_role = any(role.name in ALLOWED_ROLES for role in ctx.author.roles)
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

    # !tasks off <name> / on <name>
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
