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

# ---------------------- REJESTRACJA ----------------------
def setup(bot):

    # ---------------------- !CWEL ----------------------
    @bot.command()
    async def cwel(ctx):
        if ctx.channel.id != CWEL_CHANNEL_ID:
            return

        # 🟡 SPECJALNY PRZYPADEK — NA SAMYM POCZĄTKU
        if ctx.author.id == SPECIAL_USER_ID:
            await ctx.send(f"<@{SPECIAL_USER_ID}>, zostałeś wybrany na cwela dnia! 💀")
            return

        has_role = any(r.name in ALLOWED_ROLE_NAMES for r in ctx.author.roles)
        has_user = ctx.author.id in ALLOWED_USER_IDS

        # 🔒 BLOKADA
        if not has_role and not has_user:
            await ctx.send("Ty nie losujesz cwela — **TY JESTEŚ CWELEM NAD CWELAMI!** 💀🔥")
            return

        # 🔴 NORMALNE LOSOWANIE
        members = [
            m for m in ctx.guild.members
            if not m.bot and m.id != ctx.author.id
        ]

        if not members:
            await ctx.send("Brak użytkowników do pingnięcia.")
            return

        losowy = random.choice(members)
        await update_ranking(losowy.id)

        await ctx.send(f"{losowy.mention}, zostałeś wybrany na cwela dnia! 💀")

    # ---------------------- !SMAKI ----------------------
    @bot.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def smaki(ctx):
        if ctx.channel.id != SMAKI_CHANNEL_ID:
            await ctx.send(f"❌ Komenda działa tylko na <#{SMAKI_CHANNEL_ID}>")
            return

        has_role = any(r.name in ALLOWED_ROLE_NAMES for r in ctx.author.roles)
        has_user = ctx.author.id in ALLOWED_USER_IDS

        if has_role or has_user:
            ctx.command.reset_cooldown(ctx)

        procent = random.randint(0, 100)
        await ctx.send(f"Dzisiaj procent smaczków: {procent}% 🍬")

    # ---------------------- !RANKING ----------------------
    @bot.command()
    async def ranking(ctx):
        top = await load_top_n(10)
        msg = "🏆 **Ranking:**\n"

        for i, (uid, count) in enumerate(top, 1):
            user = await bot.fetch_user(uid)
            msg += f"{i}. {user.name} — {count}\n"

        await ctx.send(msg)

    # ---------------------- !TASKS ----------------------
    @bot.command()
    async def tasks(ctx, action=None, task_name=None):
        has_role = any(r.name in ALLOWED_ROLE_NAMES for r in ctx.author.roles)
        has_user = ctx.author.id in ALLOWED_USER_IDS

        if not has_role and not has_user:
            await ctx.send("❌ Brak uprawnień")
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
            ok, msg = await run_task(bot, task_name)
            await ctx.send(("✅ " if ok else "❌ ") + msg)
            return

        await ctx.send("❓ Użycie: `!tasks`, `!tasks on/off <nazwa>`, `!tasks run <nazwa>`")

    # ---------------------- !SWAPROLE ----------------------
    @bot.command()
    async def swaprole(ctx, user: discord.Member, role_remove: discord.Role, role_add: discord.Role):
        has_role = any(r.name in ALLOWED_ROLE_NAMES for r in ctx.author.roles)
        has_user = ctx.author.id in ALLOWED_USER_IDS

        if not has_role and not has_user:
            await ctx.send("❌ Nie masz uprawnień do tej komendy.")
            return

        # sprawdzanie hierarchii
        if role_remove >= ctx.guild.me.top_role or role_add >= ctx.guild.me.top_role:
            await ctx.send("❌ Bot nie może zarządzać jedną z tych ról.")
            return

        if role_remove in user.roles:
            await user.remove_roles(role_remove)

        if role_add not in user.roles:
            await user.add_roles(role_add)

        await ctx.send(
            f"🔄 {user.mention}\n"
            f"❌ usunięto: **{role_remove.name}**\n"
            f"✅ dodano: **{role_add.name}**"
        )
    
    print("🧩 setup(bot) URUCHOMIONY")
