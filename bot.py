import os
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import database as db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TRIVIA_QUESTIONS = [
    {"q": "ما هي عاصمة أستراليا؟", "correct": "كانبرا", "wrong": ["سيدني", "ملبورن", "بيرث"]},
    {"q": "كم عدد ألوان قوس قزح؟", "correct": "7", "wrong": ["5", "6", "8"]},
    {"q": "من اخترع المصباح الكهربائي؟", "correct": "توماس إديسون", "wrong": ["نيكولا تسلا", "أينشتاين", "غراهام بيل"]},
    {"q": "ما هو أكبر كوكب في المجموعة الشمسية؟", "correct": "المشتري", "wrong": ["زحل", "نبتون", "الأرض"]},
    {"q": "كم عدد أيام السنة الكبيسة؟", "correct": "366", "wrong": ["365", "364", "367"]},
    {"q": "ما هي أكبر دولة عربية من حيث المساحة؟", "correct": "الجزائر", "wrong": ["السعودية", "مصر", "السودان"]},
    {"q": "ما هو الحيوان الذي يلقب بسفينة الصحراء؟", "correct": "الجمل", "wrong": ["الحصان", "الفيل", "الحمار"]},
    {"q": "ما هو أسرع حيوان بري؟", "correct": "الفهد", "wrong": ["الأسد", "الحصان", "النمر"]},
]

@bot.event
async def on_ready():
    await db.init_db()
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر سلاش")
    except Exception as e:
        print("خطأ بالمزامنة:", e)
    print(f"✅ البوت شغال باسم {bot.user}")

@bot.tree.command(name="ping", description="اختبار سرعة البوت")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 بونغ! {round(bot.latency*1000)}ms")

@bot.tree.command(name="points", description="اعرض نقاطك")
async def points(interaction: discord.Interaction):
    total = await db.get_total_points(interaction.user.id, interaction.guild_id)
    await interaction.response.send_message(f"💰 نقاطك: **{total}**")

@bot.tree.command(name="daily", description="خذ مكافأتك اليومية")
async def daily(interaction: discord.Interaction):
    amount = random.randint(50, 150)
    await db.add_points(interaction.user.id, interaction.guild_id, "daily", amount)
    await interaction.response.send_message(f"🎁 حصلت على **{amount}** نقطة اليوم!")

@bot.tree.command(name="leaderboard", description="لوحة الصدارة")
@app_commands.describe(game="اسم اللعبة (اتركه فاضي للكل)")
async def leaderboard(interaction: discord.Interaction, game: str = None):
    rows = await db.get_leaderboard(interaction.guild_id, game, 10)
    if not rows:
        return await interaction.response.send_message("لا يوجد لاعبون بعد!")
    embed = discord.Embed(
        title=f"🏆 لوحة الصدارة {'- ' + game if game else '(كل الألعاب)'}",
        color=discord.Color.gold()
    )
    medals = ["🥇", "🥈", "🥉"]
    desc = ""
    for i, (uid, pts, wins) in enumerate(rows):
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        desc += f"{medal} <@{uid}> — **{pts}** نقطة ({wins} فوز)\n"
    embed.description = desc
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="إحصائيات لاعب")
async def stats(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    data = await db.get_stats(user.id, interaction.guild_id)
    if not data:
        return await interaction.response.send_message(f"{user.mention} ما لعب أي لعبة بعد!")
    embed = discord.Embed(title=f"📊 إحصائيات {user.display_name}", color=discord.Color.blue())
    for game, pts, wins, plays in data:
        embed.add_field(name=game, value=f"نقاط: {pts} | فوز: {wins} | مرات: {plays}", inline=False)
    await interaction.response.send_message(embed=embed)

class TriviaButton(discord.ui.Button):
    def __init__(self, label, correct):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.is_correct = (label == correct)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.answered:
            return await interaction.response.send_message("تم الجواب!", ephemeral=True)
        view.answered = True
        if self.is_correct:
            await db.add_points(interaction.user.id, interaction.guild_id, "trivia", 20, won=True)
            await interaction.response.send_message("✅ صح! +20 نقطة")
        else:
            await interaction.response.send_message(f"❌ غلط! الجواب: {view.correct}")
        view.stop()

class TriviaView(discord.ui.View):
    def __init__(self, correct, options):
        super().__init__(timeout=30)
        self.correct = correct
        self.answered = False
        for opt in options:
            self.add_item(TriviaButton(opt, correct))

@bot.tree.command(name="trivia", description="سؤال ثقافي سريع")
async def trivia(interaction: discord.Interaction):
    q = random.choice(TRIVIA_QUESTIONS)
    options = q["wrong"] + [q["correct"]]
    random.shuffle(options)
    view = TriviaView(q["correct"], options)
    await interaction.response.send_message(f"❓ {q['q']}", view=view)

@bot.tree.command(name="guess", description="خمن الرقم بين 1 و 100")
async def guess(interaction: discord.Interaction):
    number = random.randint(1, 100)
    await interaction.response.send_message("🎯 خمنت رقم بين 1 و 100. عندك 3 محاولات (30 ثانية لكل محاولة)")

    def check(m):
        return (m.author.id == interaction.user.id
                and m.channel.id == interaction.channel.id
                and m.content.isdigit())

    for _ in range(3):
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            return await interaction.followup.send(f"⏰ انتهى الوقت! الرقم كان **{number}**")
        g = int(msg.content)
        if g == number:
            await db.add_points(interaction.user.id, interaction.guild_id, "guess", 30, won=True)
            return await interaction.followup.send(f"🎉 صح! الرقم {number}. +30 نقطة")
        elif g < number:
            await interaction.followup.send("⬆️ أعلى")
        else:
            await interaction.followup.send("⬇️ أقل")
    await interaction.followup.send(f"❌ خلصت محاولاتك! الرقم كان **{number}**")

class HigherLowerView(discord.ui.View):
    def __init__(self, author_id, guild_id):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.guild_id = guild_id
        self.current = random.randint(1, 100)
        self.round = 0
        self.max_rounds = 5

    def make_embed(self):
        return discord.Embed(
            title="🎲 أعلى أو أقل",
            description=f"الرقم الحالي: **{self.current}**\nالجولة: {self.round}/{self.max_rounds}",
            color=discord.Color.purple()
        )

    @discord.ui.button(label="⬆️ أعلى", style=discord.ButtonStyle.success)
    async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "higher")

    @discord.ui.button(label="⬇️ أقل", style=discord.ButtonStyle.danger)
    async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "lower")

    async def play(self, interaction, choice):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("هذي لعبة غيرك!", ephemeral=True)
        new_num = random.randint(1, 100)
        correct = (choice == "higher" and new_num > self.current) or \
                  (choice == "lower" and new_num < self.current)
        self.round += 1
        if correct:
            self.current = new_num
            if self.round >= self.max_rounds:
                await db.add_points(self.author_id, self.guild_id, "higherlower", 50, won=True)
                await interaction.response.edit_message(
                    content=f"🏆 أكملت {self.max_rounds} جولات! +50 نقطة",
                    embed=None, view=None
                )
                return self.stop()
            await interaction.response.edit_message(embed=self.make_embed(), view=self)
        else:
            reward = self.round * 5
            await db.add_points(self.author_id, self.guild_id, "higherlower", reward)
            await interaction.response.edit_message(
                content=f"❌ غلط! الرقم كان {new_num}. ربحت {reward} نقطة",
                embed=None, view=None
            )
            self.stop()

@bot.tree.command(name="higherlower", description="أعلى أو أقل")
async def higherlower(interaction: discord.Interaction):
    view = HigherLowerView(interaction.user.id, interaction.guild_id)
    await interaction.response.send_message(embed=view.make_embed(), view=view)

if __name__ == "__main__":
    bot.run(TOKEN)
