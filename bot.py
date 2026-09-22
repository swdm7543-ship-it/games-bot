import os
import random
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import database as db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=".", intents=intents)

# ================== المتجر ==================
SHOP = {
    "روليت": {
        "حظ":        {"price": 200, "desc": "🍀 يزيد فرصة نجاتك بالقرعة"},
        "حصانة":     {"price": 500, "desc": "🛡️ يحميك من أول رصاصة"},
        "رصاصة_ذهبية": {"price": 800, "desc": "🎯 تختار لاعباً ليخرج فوراً"},
    },
    "مافيا": {
        "تلميح":     {"price": 150, "desc": "🔍 يعطيك 3 أسماء أحدهم مافيا"},
        "كشف":       {"price": 400, "desc": "👁️ يكشف دور لاعب عشوائي"},
        "حماية":     {"price": 600, "desc": "🛡️ يحميك من القتل لليلة"},
    },
    "انفجار": {
        "وقت":       {"price": 100, "desc": "⏱️ +10 ثواني إضافية"},
        "تخطي":      {"price": 250, "desc": "🔄 يغير لك الحرف"},
        "مضاعف":     {"price": 400, "desc": "✖️ يضاعف نقاطك"},
    },
    "تخمين": {
        "محاولة":    {"price": 150, "desc": "➕ محاولة إضافية"},
        "تلميح":     {"price": 100, "desc": "🔍 يقربك من الرقم"},
    },
    "حجرة": {
        "نظرة":      {"price": 200, "desc": "👁️ يشوف اختيار البوت مسبقاً"},
        "إعادة":     {"price": 300, "desc": "🔄 يعيد الجولة إذا خسرت"},
    },
}

TRIVIA_QUESTIONS = [
    {"q": "ما هي عاصمة أستراليا؟", "correct": "كانبرا", "wrong": ["سيدني", "ملبورن", "بيرث"]},
    {"q": "كم عدد ألوان قوس قزح؟", "correct": "7", "wrong": ["5", "6", "8"]},
    {"q": "من اخترع المصباح الكهربائي؟", "correct": "توماس إديسون", "wrong": ["نيكولا تسلا", "أينشتاين", "غراهام بيل"]},
    {"q": "ما هو أكبر كوكب في المجموعة الشمسية؟", "correct": "المشتري", "wrong": ["زحل", "نبتون", "الأرض"]},
    {"q": "كم عدد أيام السنة الكبيسة؟", "correct": "366", "wrong": ["365", "364", "367"]},
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

# ================== أوامر عامة ==================
@bot.command(name="نقاطي", aliases=["points"])
async def points(ctx):
    total = await db.get_total_points(ctx.author.id, ctx.guild.id)
    await ctx.send(f"💰 نقاطك يا {ctx.author.mention}: **{total}**")

@bot.command(name="يومي", aliases=["daily"])
async def daily(ctx):
    amount = random.randint(50, 150)
    await db.add_points(ctx.author.id, ctx.guild.id, "daily", amount)
    await ctx.send(f"🎁 حصلت على **{amount}** نقطة اليوم!")

@bot.command(name="صدارة", aliases=["leaderboard"])
async def leaderboard(ctx, game: str = None):
    rows = await db.get_leaderboard(ctx.guild.id, game, 10)
    if not rows:
        return await ctx.send("لا يوجد لاعبون بعد!")
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
    await ctx.send(embed=embed)

@bot.command(name="صدارة_لعب")
async def leaderboard_plays(ctx):
    rows = await db.get_leaderboard_plays(ctx.guild.id, 10)
    if not rows:
        return await ctx.send("لا يوجد لاعبون بعد!")
    embed = discord.Embed(title="🎮 الأكثر لعباً", color=discord.Color.purple())
    medals = ["🥇", "🥈", "🥉"]
    desc = ""
    for i, (uid, plays) in enumerate(rows):
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        desc += f"{medal} <@{uid}> — **{plays}** مرة\n"
    embed.description = desc
    await ctx.send(embed=embed)

@bot.command(name="حقيبتي", aliases=["inventory"])
async def inventory(ctx):
    items = await db.get_inventory(ctx.author.id, ctx.guild.id)
    if not items:
        return await ctx.send("🎒 حقيبتك فاضية! اشترِ من المتجر.")
    embed = discord.Embed(title=f"🎒 حقيبة {ctx.author.display_name}", color=discord.Color.teal())
    for item_id, game, qty in items:
        embed.add_field(name=f"{item_id} ({game})", value=f"الكمية: {qty}", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="متجر")
async def shop(ctx, game: str = None):
    if game is None:
        embed = discord.Embed(
            title="🛒 المتجر",
            description="اختر لعبة: " + " | ".join(f"`.متجر {g}`" for g in SHOP.keys()),
            color=discord.Color.dark_green()
        )
        return await ctx.send(embed=embed)
    game = game.strip()
    if game not in SHOP:
        return await ctx.send("❌ هذه اللعبة غير موجودة في المتجر.")
    embed = discord.Embed(title=f"🛒 متجر {game}", color=discord.Color.dark_green())
    for item_id, info in SHOP[game].items():
        embed.add_field(
            name=f"{info['desc']} — `{item_id}`",
            value=f"السعر: **{info['price']}** نقطة",
            inline=False
        )
    embed.set_footer(text=f"للشراء: .اشتري {game} اسم_العنصر")
    await ctx.send(embed=embed)

@bot.command(name="اشتري", aliases=["buy"])
async def buy(ctx, game: str, item_id: str):
    game = game.strip()
    item_id = item_id.strip()
    if game not in SHOP or item_id not in SHOP[game]:
        return await ctx.send("❌ هذا العنصر غير موجود.")
    price = SHOP[game][item_id]["price"]
    ok = await db.deduct_points(ctx.author.id, ctx.guild.id, price)
    if not ok:
        return await ctx.send(f"❌ ما عندك نقاط كافية! تحتاج **{price}** نقطة.")
    await db.add_item(ctx.author.id, ctx.guild.id, item_id, game)
    await ctx.send(f"✅ اشتريت **{item_id}** من متجر **{game}** بـ {price} نقطة!")

# ================== روليت ==================
class RouletteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.players = []
        self.started = False

    @discord.ui.button(label="انضم", style=discord.ButtonStyle.success, emoji="🔫")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [p.id for p in self.players]:
            self.players.append(interaction.user)
            await interaction.response.send_message(f"✅ انضم {interaction.user.mention}!", ephemeral=False)
        else:
            await interaction.response.send_message("أنت مسجل!", ephemeral=True)

    @discord.ui.button(label="ابدأ", style=discord.ButtonStyle.danger, emoji="💥")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.players) < 2:
            return await interaction.response.send_message("تحتاج لاعبين على الأقل.", ephemeral=True)
        if self.started:
            return await interaction.response.send_message("بدأت!", ephemeral=True)
        self.started = True
        await interaction.response.send_message("🔫 **بدأت اللعبة!**")
        await asyncio.sleep(2)
        alive = self.players.copy()
        immune = set()
        # فحص الحصانة
        for p in alive.copy():
            if await db.has_item(p.id, interaction.guild.id, "حصانة") > 0:
                await db.use_item(p.id, interaction.guild.id, "حصانة")
                immune.add(p.id)
                await interaction.channel.send(f"🛡️ {p.mention} استخدم حصانة!")
        while len(alive) > 1:
            victim = random.choice([p for p in alive if p.id not in immune]) if any(p.id not in immune for p in alive) else random.choice(alive)
            alive.remove(victim)
            await interaction.channel.send(f"💥 **بانغ!** {victim.mention} خرج!")
            await asyncio.sleep(2)
        winner = alive[0]
        await db.add_points(winner.id, interaction.guild.id, "روليت", 100, won=True)
        await interaction.channel.send(f"🏆 الفائز: {winner.mention} — **+100 نقطة**")
        self.stop()

@bot.command(name="روليت")
async def roulette(ctx):
    embed = discord.Embed(title="🔫 الروليت الروسية", description="انضم وابدأ. الفائز +100 نقطة.", color=discord.Color.dark_red())
    embed.set_image(url="https://i.imgur.com/8Q9Z9Qp.png")
    await ctx.send(embed=embed, view=RouletteView())

# ================== انفجار الكلمة ==================
@bot.command(name="انفجار")
async def bomb_party(ctx):
    letters = ["ا","ب","ت","ج","ح","خ","د","ر","س","ش","ص","ط","ع","ف","ق","ك","ل","م","ن","ه","و","ي"]
    letter = random.choice(letters)
    embed = discord.Embed(title="💣 انفجار الكلمة", description=f"اكتب كلمة تبدأ بـ **{letter}** بأسرع وقت!\n+30 نقطة", color=discord.Color.orange())
    await ctx.send(embed=embed)
    def check(m):
        return m.channel == ctx.channel and m.content.startswith(letter) and len(m.content) > 2
    try:
        msg = await bot.wait_for("message", check=check, timeout=20)
        await db.add_points(msg.author.id, ctx.guild.id, "انفجار", 30, won=True)
        await ctx.send(f"🎉 مبروك {msg.author.mention}! +30 نقطة")
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ انتهى الوقت! الحرف كان **{letter}**")

# ================== تخمين الرقم ==================
@bot.command(name="تخمين")
async def guess(ctx):
    number = random.randint(1, 100)
    extra = await db.has_item(ctx.author.id, ctx.guild.id, "محاولة")
    tries = 3 + extra
    if extra > 0:
        await db.use_item(ctx.author.id, ctx.guild.id, "محاولة")
    await ctx.send(f"🎯 خمن رقم بين 1 و 100. عندك **{tries}** محاولات.")
    def check(m):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.isdigit()
    for _ in range(tries):
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            return await ctx.send(f"⏰ انتهى الوقت! الرقم كان **{number}**")
        g = int(msg.content)
        if g == number:
            await db.add_points(ctx.author.id, ctx.guild.id, "تخمين", 30, won=True)
            return await ctx.send(f"🎉 صح! +30 نقطة")
        elif g < number:
            await ctx.send("⬆️ أعلى")
        else:
            await ctx.send("⬇️ أقل")
    await ctx.send(f"❌ خلصت! الرقم كان **{number}**")

# ================== حجرة ورقة مقص ==================
class RPSView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=30)
        self.author_id = author_id
    async def play(self, interaction, choice):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("لعبة غيرك!", ephemeral=True)
        bot_choice = random.choice(["حجرة","ورقة","مقص"])
        if choice == bot_choice:
            result = "🤝 تعادل!"
        elif (choice=="حجرة" and bot_choice=="مقص") or (choice=="ورقة" and bot_choice=="حجرة") or (choice=="مقص" and bot_choice=="ورقة"):
            result = "🎉 فزت! +10 نقاط"
            await db.add_points(self.author_id, interaction.guild.id, "حجرة", 10, won=True)
        else:
            result = "❌ خسرت!"
        await interaction.response.edit_message(embed=discord.Embed(title="🎮 حجرة ورقة مقص", description=f"اخترت: **{choice}**\nالبوت: **{bot_choice}**\n\n{result}", color=discord.Color.blue()), view=None)
        self.stop()
    @discord.ui.button(label="🪨 حجرة", style=discord.ButtonStyle.secondary)
    async def rock(self, i, b): await self.play(i, "حجرة")
    @discord.ui.button(label="📄 ورقة", style=discord.ButtonStyle.secondary)
    async def paper(self, i, b): await self.play(i, "ورقة")
    @discord.ui.button(label="✂️ مقص", style=discord.ButtonStyle.secondary)
    async def scissors(self, i, b): await self.play(i, "مقص")

@bot.command(name="حجرة")
async def rps(ctx):
    await ctx.send(embed=discord.Embed(title="🎮 حجرة ورقة مقص", description="اختر سلاحك!", color=discord.Color.green()), view=RPSView(ctx.author.id))

# ================== أعلى أو أقل ==================
class HigherLowerView(discord.ui.View):
    def __init__(self, author_id, guild_id):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.guild_id = guild_id
        self.current = random.randint(1, 100)
        self.round = 0
        self.max = 5
    def make_embed(self):
        return discord.Embed(title="🎲 أعلى أو أقل", description=f"الرقم الحالي: **{self.current}**\nالجولة: {self.round}/{self.max}", color=discord.Color.purple())
    async def play(self, interaction, choice):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("لعبة غيرك!", ephemeral=True)
        new_num = random.randint(1, 100)
        correct = (choice=="higher" and new_num > self.current) or (choice=="lower" and new_num < self.current)
        self.round += 1
        if correct:
            self.current = new_num
            if self.round >= self.max:
                await db.add_points(self.author_id, self.guild_id, "اعلى_او_اقل", 50, won=True)
                return await interaction.response.edit_message(content="🏆 أكملت! +50 نقطة", embed=None, view=None)
            await interaction.response.edit_message(embed=self.make_embed(), view=self)
        else:
            reward = self.round * 5
            await db.add_points(self.author_id, self.guild_id, "اعلى_او_اقل", reward)
            await interaction.response.edit_message(content=f"❌ غلط! الرقم كان {new_num}. +{reward} نقطة", embed=None, view=None)
            self.stop()
    @discord.ui.button(label="⬆️ أعلى", style=discord.ButtonStyle.success)
    async def higher(self, i, b): await self.play(i, "higher")
    @discord.ui.button(label="⬇️ أقل", style=discord.ButtonStyle.danger)
    async def lower(self, i, b): await self.play(i, "lower")

@bot.command(name="اعلى")
async def higher_lower(ctx):
    v = HigherLowerView(ctx.author.id, ctx.guild.id)
    await ctx.send(embed=v.make_embed(), view=v)

# ================== سرعة الكتابة ==================
@bot.command(name="سرعة")
async def speed(ctx):
    phrases = ["البرمجة ممتعة جداً", "ديسكورد بوت رهيب", "أنا أحب الألعاب", "التعلم مستمر", "الرياضيات ذكاء", "القراءة غذاء العقل"]
    phrase = random.choice(phrases)
    await ctx.send(f"⌨️ اكتب الجملة التالية بأسرع ما يمكن:\n**{phrase}**")
    def check(m):
        return m.channel == ctx.channel and m.content.strip() == phrase
    try:
        msg = await bot.wait_for("message", check=check, timeout=20)
        await db.add_points(msg.author.id, ctx.guild.id, "سرعة", 25, won=True)
        await ctx.send(f"⚡ مبروك {msg.author.mention}! +25 نقطة")
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ انتهى الوقت! الجملة كانت: **{phrase}**")

# ================== سلسلة الكلمات ==================
@bot.command(name="سلسلة")
async def chain(ctx, starting_letter: str = None):
    letter = starting_letter or random.choice(["ا","ب","ت","ج","ح","د","ر","س","ع","ف","ك","ل","م","ن","ه","و","ي"])
    await ctx.send(f"🔗 اكتب كلمة تبدأ بحرف **{letter}** (المشاركون يتابعون بالتناوب).")
    used = set()
    last_letter = letter
    end_time = 30
    def check(m):
        return m.channel == ctx.channel and len(m.content) > 1 and m.content[0] == last_letter and m.content not in used
    while True:
        try:
            msg = await bot.wait_for("message", check=check, timeout=end_time)
            used.add(msg.content)
            last_letter = msg.content[-1]
            await db.add_points(msg.author.id, ctx.guild.id, "سلسلة", 10)
            await ctx.send(f"✅ صحيح! الحرف التالي: **{last_letter}**")
            end_time = 20
        except asyncio.TimeoutError:
            await ctx.send("⏰ انتهت السلسلة!")
            break

# ================== بينغو ==================
@bot.command(name="بينغو")
async def bingo(ctx):
    numbers = random.sample(range(1, 51), 5)
    embed = discord.Embed(title="🎱 بينغو", description=f"أرقامك: **{', '.join(map(str, numbers))}**\nسيتم سحب 5 أرقام عشوائية...", color=discord.Color.gold())
    await ctx.send(embed=embed)
    await asyncio.sleep(3)
    drawn = random.sample(range(1, 51), 5)
    matched = sum(1 for n in numbers if n in drawn)
    points = matched * 15
    if points > 0:
        await db.add_points(ctx.author.id, ctx.guild.id, "بينغو", points, won=(matched>=3))
    await ctx.send(f"🎲 الأرقام المسحوبة: **{', '.join(map(str, drawn))}**\nتطابق: **{matched}**\nربحت: **{points}** نقطة")

# ================== مافيا ==================
class MafiaView(discord.ui.View):
    def __init__(self, host):
        super().__init__(timeout=120)
        self.host = host
        self.players = []
        self.started = False
    @discord.ui.button(label="انضم", style=discord.ButtonStyle.primary, emoji="🕵️")
    async def join(self, interaction, button):
        if interaction.user.id not in [p.id for p in self.players]:
            self.players.append(interaction.user)
            await interaction.response.send_message(f"✅ انضم {interaction.user.mention}!", ephemeral=False)
        else:
            await interaction.response.send_message("مسجل!", ephemeral=True)
    @discord.ui.button(label="ابدأ", style=discord.ButtonStyle.danger, emoji="🔪")
    async def start(self, interaction, button):
        if interaction.user.id != self.host.id:
            return await interaction.response.send_message("فقط منشئ اللعبة!", ephemeral=True)
        if len(self.players) < 4:
            return await interaction.response.send_message("تحتاج 4 لاعبين!", ephemeral=True)
        self.started = True
        await interaction.response.send_message("🕵️ **بدأت المافيا!** سيتم إرسال الأدوار بالخاص.", ephemeral=True)
        mafia_count = max(1, len(self.players) // 4)
        mafia_members = random.sample(self.players, mafia_count)
        for p in self.players:
            try:
                if p in mafia_members:
                    await p.send("🔪 أنت **مافيا**!")
                else:
                    await p.send("👨‍🌾 أنت **مواطن صالح**!")
            except:
                await interaction.channel.send(f"⚠️ {p.mention} الخاص مغلق.")
        await asyncio.sleep(2)
        await interaction.channel.send(f"🗳️ المافيا هم: ||{' , '.join(m.name for m in mafia_members)}||\n(لعبة تجريبية)")
        self.stop()

@bot.command(name="مافيا")
async def mafia(ctx):
    embed = discord.Embed(title="🕵️ المافيا", description="انضم (4 لاعبين على الأقل).", color=discord.Color.dark_purple())
    embed.set_image(url="https://i.imgur.com/kY6W4k8.png")
    await ctx.send(embed=embed, view=MafiaView(ctx.author))

if __name__ == "__main__":
    bot.run(TOKEN)
