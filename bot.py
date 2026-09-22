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
intents.members = True
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ================== المتجر ==================
SHOP = {
    "روليت": {
        "حظ":          {"price": 200, "emoji": "🍀", "desc": "يزيد فرصة نجاتك"},
        "حصانة":       {"price": 500, "emoji": "🛡️", "desc": "يحميك من أول رصاصة"},
        "رصاصة_ذهبية":  {"price": 800, "emoji": "🎯", "desc": "تختار من يخرج أول"},
    },
    "مافيا": {
        "تلميح":       {"price": 150, "emoji": "🔍", "desc": "3 أسماء أحدهم مافيا"},
        "كشف":         {"price": 400, "emoji": "👁️", "desc": "يكشف دور لاعب عشوائي"},
        "حماية":       {"price": 600, "emoji": "🛡️", "desc": "يحماك لليلة"},
    },
    "انفجار": {
        "وقت":         {"price": 100, "emoji": "⏱️", "desc": "+10 ثواني"},
        "تخطي":        {"price": 250, "emoji": "🔄", "desc": "يغير الحرف"},
        "مضاعف":       {"price": 400, "emoji": "✖️", "desc": "يضاعف النقاط"},
    },
    "تخمين": {
        "محاولة":      {"price": 150, "emoji": "➕", "desc": "محاولة إضافية"},
        "تلميح":       {"price": 100, "emoji": "🔍", "desc": "يقربك من الرقم"},
    },
    "حجرة": {
        "نظرة":        {"price": 200, "emoji": "👁️", "desc": "يشوف اختيار البوت"},
        "إعادة":       {"price": 300, "emoji": "🔄", "desc": "يعيد الجولة"},
    },
}

# ================== كلمات للألعاب ==================
HANGMAN_WORDS = ["برمجة", "ديسكورد", "سيارة", "مدرسة", "مكتبة", "كمبيوتر", "تفاحة", "شمس", "قمر", "نجمة"]
SCRAMBLE_WORDS = ["سلام", "كتاب", "قلم", "حاسوب", "هاتف", "بحر", "جبل", "سماء", "وردة", "شجرة"]
WYR_QUESTIONS = [
    ("تكون غني لكن وحيد", "تكون فقير لكن محبوب"),
    ("تعيش في المستقبل", "تعيش في الماضي"),
    ("تأكل نفس الأكل للأبد", "تسمع نفس الأغنية للأبد"),
    ("تصير مشهور", "تصير ذكي خارق"),
    ("تطير", "تصير غير مرئي"),
]
NHIE_QUESTIONS = [
    "عمري ما كذبت على صديق",
    "عمري ما نمت في الحصة",
    "عمري ما أكلت أكل أحد بدون إذن",
    "عمري ما نسيت عيد ميلاد أحد",
    "عمري ما سويت شي محرج قدام الناس",
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
@bot.hybrid_command(name="نقاطي", description="اعرض نقاطك")
async def points(ctx):
    total = await db.get_total_points(ctx.author.id, ctx.guild.id)
    await ctx.send(f"💰 نقاطك يا {ctx.author.mention}: **{total}**")

@bot.hybrid_command(name="يومي", description="خذ مكافأتك اليومية")
async def daily(ctx):
    amount = random.randint(50, 150)
    await db.add_points(ctx.author.id, ctx.guild.id, "daily", amount)
    await ctx.send(f"🎁 حصلت على **{amount}** نقطة اليوم!")

@bot.hybrid_command(name="صدارة", description="لوحة الصدارة")
async def leaderboard(ctx, game: str = None):
    rows = await db.get_leaderboard(ctx.guild.id, game, 10)
    if not rows:
        return await ctx.send("لا يوجد لاعبون بعد!")
    embed = discord.Embed(title=f"🏆 لوحة الصدارة {'- ' + game if game else '(كل الألعاب)'}", color=discord.Color.gold())
    medals = ["🥇", "🥈", "🥉"]
    desc = ""
    for i, (uid, pts, wins) in enumerate(rows):
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        desc += f"{medal} <@{uid}> — **{pts}** نقطة ({wins} فوز)\n"
    embed.description = desc
    await ctx.send(embed=embed)

@bot.hybrid_command(name="صدارة_لعب", description="الأكثر لعباً")
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

@bot.hybrid_command(name="حقيبتي", description="اعرض مشترياتك")
async def inventory(ctx):
    items = await db.get_inventory(ctx.author.id, ctx.guild.id)
    if not items:
        return await ctx.send("🎒 حقيبتك فاضية! اشترِ من المتجر.")
    embed = discord.Embed(title=f"🎒 حقيبة {ctx.author.display_name}", color=discord.Color.teal())
    for item_id, game, qty in items:
        embed.add_field(name=f"{item_id} ({game})", value=f"الكمية: {qty}", inline=True)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="متجر", description="متجر الألعاب")
async def shop(ctx, game: str = None):
    if game is None:
        games_list = " | ".join(f"`.متجر {g}`" for g in SHOP.keys())
        return await ctx.send(embed=discord.Embed(title="🛒 المتجر", description=f"اختر لعبة:\n{games_list}", color=discord.Color.dark_green()))
    game = game.strip()
    if game not in SHOP:
        return await ctx.send("❌ هذه اللعبة غير موجودة.")
    embed = discord.Embed(title=f"🛒 متجر {game}", color=discord.Color.dark_green())
    for item_id, info in SHOP[game].items():
        embed.add_field(name=f"{info['emoji']} {item_id}", value=f"{info['desc']} — **{info['price']}** نقطة", inline=False)
    embed.set_footer(text=f"للشراء: .اشتري {game} اسم_العنصر")
    await ctx.send(embed=embed)

@bot.hybrid_command(name="اشتري", description="اشترِ عنصر من المتجر")
async def buy(ctx, game: str, item_id: str):
    game = game.strip()
    item_id = item_id.strip()
    if game not in SHOP or item_id not in SHOP[game]:
        return await ctx.send("❌ هذا العنصر غير موجود.")
    price = SHOP[game][item_id]["price"]
    ok = await db.deduct_points(ctx.author.id, ctx.guild.id, price)
    if not ok:
        return await ctx.send(f"❌ ما عندك نقاط كافية! تحتاج **{price}**.")
    await db.add_item(ctx.author.id, ctx.guild.id, item_id, game)
    await ctx.send(f"✅ اشتريت **{item_id}** بـ {price} نقطة!")

# ================== روليت (Emoji Visual) ==================
class RouletteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.players = []
        self.started = False

    @discord.ui.button(label="انضم", style=discord.ButtonStyle.success, emoji="🔫")
    async def join(self, interaction, button):
        if interaction.user.id not in [p.id for p in self.players]:
            self.players.append(interaction.user)
            await interaction.response.send_message(f"✅ انضم {interaction.user.mention}!", ephemeral=False)
        else:
            await interaction.response.send_message("مسجل!", ephemeral=True)

    @discord.ui.button(label="ابدأ", style=discord.ButtonStyle.danger, emoji="💥")
    async def start(self, interaction, button):
        if len(self.players) < 2:
            return await interaction.response.send_message("تحتاج لاعبين على الأقل!", ephemeral=True)
        if self.started:
            return await interaction.response.send_message("بدأت!", ephemeral=True)
        self.started = True
        await interaction.response.send_message("🔫 **بدأت اللعبة!**")
        await asyncio.sleep(2)
        alive = self.players.copy()
        chambers = ["🔘", "🔘", "🔘", "🔘", "🔘", "💥"]
        random.shuffle(chambers)

        while len(alive) > 1:
            victim = random.choice(alive)
            alive.remove(victim)
            board = "".join(random.sample(chambers, len(chambers)))
            await interaction.channel.send(f"🎯 **سحب الزناد...**\n{board}\n💥 **بانغ!** {victim.mention} خرج!")
            await asyncio.sleep(2)

        winner = alive[0]
        await db.add_points(winner.id, interaction.guild.id, "روليت", 100, won=True)
        embed = discord.Embed(
            title="🏆 الفائز!",
            description=f"🔫 {winner.mention} نجا وحصل على **100** نقطة!\n\n`[🔘][🔘][🔘][🔘][🔘][🔘]`",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed)
        self.stop()

@bot.hybrid_command(name="روليت", description="الروليت الروسية الجماعية")
async def roulette(ctx):
    embed = discord.Embed(
        title="🔫 الروليت الروسية",
        description="🔘🔘🔘🔘🔘💥\n\nاضغط **انضم** ثم **ابدأ**.\nالفائز: **+100 نقطة**",
        color=discord.Color.dark_red()
    )
    await ctx.send(embed=embed, view=RouletteView())

# ================== حجرة ورقة مقص (ضد بوت أو لاعب) ==================
class RPSView(discord.ui.View):
    def __init__(self, p1_id, p2_id=None, p2_name=None):
        super().__init__(timeout=60)
        self.p1 = p1_id
        self.p2 = p2_id
        self.p2_name = p2_name
        self.choices = {}

    async def finish(self, interaction):
        if self.p1 in self.choices and self.p2 in self.choices:
            c1 = self.choices[self.p1]
            c2 = self.choices[self.p2]
            emoji = {"حجرة": "🪨", "ورقة": "📄", "مقص": "✂️"}
            result = ""
            if c1 == c2:
                result = "🤝 تعادل!"
            elif (c1=="حجرة" and c2=="مقص") or (c1=="ورقة" and c2=="حجرة") or (c1=="مقص" and c2=="ورقة"):
                result = f"🎉 فاز <@{self.p1}>!"
                await db.add_points(self.p1, interaction.guild.id, "حجرة", 15, won=True)
            else:
                result = f"🎉 فاز <@{self.p2}>!"
                if self.p2 != "BOT":
                    await db.add_points(self.p2, interaction.guild.id, "حجرة", 15, won=True)
            embed = discord.Embed(
                title="🎮 النتيجة",
                description=f"<@{self.p1}>: {emoji[c1]} {c1}\n<@{self.p2}>: {emoji[c2]} {c2}\n\n**{result}**",
                color=discord.Color.green()
            )
            await interaction.channel.send(embed=embed)
            self.stop()

    @discord.ui.button(label="حجرة", emoji="🪨")
    async def rock(self, i, b): await self.pick(i, "حجرة")
    @discord.ui.button(label="ورقة", emoji="📄")
    async def paper(self, i, b): await self.pick(i, "ورقة")
    @discord.ui.button(label="مقص", emoji="✂️")
    async def scissors(self, i, b): await self.pick(i, "مقص")

    async def pick(self, interaction, choice):
        uid = interaction.user.id
        if uid not in (self.p1, self.p2):
            return await interaction.response.send_message("هذي لعبة غيرك!", ephemeral=True)
        if uid in self.choices:
            return await interaction.response.send_message("اخترت بالفعل!", ephemeral=True)
        self.choices[uid] = choice
        await interaction.response.send_message(f"✅ اخترت {choice}", ephemeral=True)

        if self.p2 == "BOT" and self.p1 in self.choices:
            self.choices["BOT"] = random.choice(["حجرة", "ورقة", "مقص"])
            await self.finish(interaction)
        elif self.p1 in self.choices and self.p2 in self.choices:
            await self.finish(interaction)

@bot.hybrid_command(name="حجرة", description="حجرة ورقة مقص (ضد بوت أو لاعب)")
async def rps(ctx, opponent: discord.Member = None):
    if opponent is None:
        view = RPSView(ctx.author.id, "BOT", "البوت")
        embed = discord.Embed(title="🎮 حجرة ورقة مقص", description=f"{ctx.author.mention} ضد 🤖 **البوت**\n\nاختر!", color=discord.Color.green())
    elif opponent.id == ctx.author.id:
        return await ctx.send("ما تقدر تلعب ضد نفسك!")
    else:
        view = RPSView(ctx.author.id, opponent.id, opponent.display_name)
        embed = discord.Embed(title="🎮 حجرة ورقة مقص", description=f"{ctx.author.mention} ضد {opponent.mention}\n\nكلاكما اخترا!", color=discord.Color.green())
    await ctx.send(embed=embed, view=view)

# ================== تخمين الرقم ==================
@bot.hybrid_command(name="تخمين", description="خمن الرقم بين 1 و 100")
async def guess(ctx):
    number = random.randint(1, 100)
    extra = await db.has_item(ctx.author.id, ctx.guild.id, "محاولة")
    tries = 3 + extra
    if extra > 0:
        await db.use_item(ctx.author.id, ctx.guild.id, "محاولة")
    await ctx.send(f"🎯 خمنت رقم بين 1 و 100. عندك **{tries}** محاولات.")
    def check(m):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.isdigit()
    for i in range(tries):
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            return await ctx.send(f"⏰ انتهى الوقت! الرقم كان **{number}**")
        g = int(msg.content)
        if g == number:
            await db.add_points(ctx.author.id, ctx.guild.id, "تخمين", 30, won=True)
            return await ctx.send(f"🎉 صح! +30 نقطة")
        elif g < number:
            await ctx.send(f"⬆️ أعلى ({tries-i-1} متبقي)")
        else:
            await ctx.send(f"⬇️ أقل ({tries-i-1} متبقي)")
    await ctx.send(f"❌ خلصت! الرقم كان **{number}**")

# ================== انفجار الكلمة ==================
@bot.hybrid_command(name="انفجار", description="اكتب كلمة تبدأ بحرف معين بسرعة")
async def bomb_party(ctx):
    letters = list("ابتجحخدرسشصطعفقكلمنهوي")
    letter = random.choice(letters)
    embed = discord.Embed(
        title="💣 انفجار الكلمة",
        description=f"💥 اكتب كلمة تبدأ بحرف **{letter}** في 20 ثانية!\n\n`[⏱️ 20s] [💥]`\n\nالجائزة: **+30 نقطة**",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)
    def check(m):
        return m.channel == ctx.channel and m.content.startswith(letter) and len(m.content) > 2
    try:
        msg = await bot.wait_for("message", check=check, timeout=20)
        await db.add_points(msg.author.id, ctx.guild.id, "انفجار", 30, won=True)
        await ctx.send(f"🎉 مبروك {msg.author.mention}! كلمة **{msg.content}** صحيحة. +30")
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ انتهى الوقت! الحرف كان **{letter}**")

# ================== هانجمان (المشنوق) ==================
@bot.hybrid_command(name="مشنوق", description="لعبة تخمين الحروف")
async def hangman(ctx):
    word = random.choice(HANGMAN_WORDS)
    guessed = set()
    tries = 6
    display = " ".join("_" if c not in guessed else c for c in word)
    stages = ["😀", "😐", "😟", "😰", "😨", "😱", "💀"]

    while tries > 0 and "_" in display:
        embed = discord.Embed(
            title="🎯 المشنوق",
            description=f"{stages[6-tries]}\n\n**{display}**\n\nالحروف المجربة: {' '.join(sorted(guessed)) or 'لا شيء'}\nالمحاولات: **{tries}**",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and len(m.content) == 1 and m.content.isalpha()
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            return await ctx.send(f"⏰ انتهى الوقت! الكلمة: **{word}**")
        c = msg.content
        if c in guessed:
            await ctx.send("جربت هذا الحرف!")
            continue
        guessed.add(c)
        if c in word:
            await ctx.send("✅ حرف صحيح!")
        else:
            tries -= 1
            await ctx.send(f"❌ غلط! متبقي {tries}")
        display = " ".join("_" if ch not in guessed else ch for ch in word)

    if "_" not in display:
        await db.add_points(ctx.author.id, ctx.guild.id, "مشنوق", 40, won=True)
        await ctx.send(f"🎉 فزت! الكلمة: **{word}** — +40 نقطة")
    else:
        await ctx.send(f"💀 خسرت! الكلمة كانت: **{word}**")

# ================== خلط الكلمات ==================
@bot.hybrid_command(name="خلط", description="رتب الحروف لتكوين كلمة")
async def scramble(ctx):
    word = random.choice(SCRAMBLE_WORDS)
    letters = list(word)
    random.shuffle(letters)
    scrambled = " ".join(letters)
    await ctx.send(f"🔤 رتب الحروف: **{scrambled}**\nعندك 20 ثانية!")
    def check(m):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for("message", check=check, timeout=20)
        if msg.content.strip() == word:
            await db.add_points(ctx.author.id, ctx.guild.id, "خلط", 25, won=True)
            await ctx.send(f"🎉 صح! +25 نقطة")
        else:
            await ctx.send(f"❌ غلط! الكلمة كانت: **{word}**")
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ انتهى الوقت! الكلمة: **{word}**")

# ================== Would You Rather ==================
class WYRView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.q = random.choice(WYR_QUESTIONS)
        self.votes_a = 0
        self.votes_b = 0
        self.voters = set()

    @discord.ui.button(label="خيار أ", style=discord.ButtonStyle.primary)
    async def a(self, i, b):
        if i.user.id in self.voters:
            return await i.response.send_message("صوتك مسجل!", ephemeral=True)
        self.voters.add(i.user.id)
        self.votes_a += 1
        await i.response.send_message(f"✅ صوت للخيار أ", ephemeral=True)
    @discord.ui.button(label="خيار ب", style=discord.ButtonStyle.success)
    async def b_btn(self, i, b):
        if i.user.id in self.voters:
            return await i.response.send_message("صوتك مسجل!", ephemeral=True)
        self.voters.add(i.user.id)
        self.votes_b += 1
        await i.response.send_message(f"✅ صوت للخيار ب", ephemeral=True)

@bot.hybrid_command(name="هذا_او_ذاك", description="هذا أو ذاك (جماعي)")
async def wyr(ctx):
    view = WYRView()
    embed = discord.Embed(
        title="🤔 هذا أو ذاك",
        description=f"**أ:** {view.q[0]}\n\n**ب:** {view.q[1]}\n\nصوّت!",
        color=discord.Color.purple()
    )
    msg = await ctx.send(embed=embed, view=view)
    await asyncio.sleep(30)
    embed.add_field(name="النتيجة", value=f"أ: **{view.votes_a}** صوت\nب: **{view.votes_b}** صوت", inline=False)
    await msg.edit(embed=embed, view=None)
    view.stop()

# ================== Never Have I Ever ==================
@bot.hybrid_command(name="عمري_ما", description="عمري ما (جماعي)")
async def nhie(ctx):
    q = random.choice(NHIE_QUESTIONS)
    embed = discord.Embed(title="🙊 عمري ما", description=f"**{q}**\n\nتفاعل بـ ✅ إذا سويتها، ❌ إذا لا", color=discord.Color.orange())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

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
        return discord.Embed(
            title="🎲 أعلى أو أقل",
            description=f"الرقم: **{self.current}**\nالجولة: {self.round}/{self.max}\n\nهل الرقم القادم أعلى أو أقل؟",
            color=discord.Color.purple()
        )
    async def play(self, interaction, choice):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("لعبة غيرك!", ephemeral=True)
        new_num = random.randint(1, 100)
        while new_num == self.current:
            new_num = random.randint(1, 100)
        correct = (choice=="higher" and new_num > self.current) or (choice=="lower" and new_num < self.current)
        self.round += 1
        if correct:
            self.current = new_num
            if self.round >= self.max:
                await db.add_points(self.author_id, self.guild_id, "اعلى_او_اقل", 50, won=True)
                return await interaction.response.edit_message(content="🏆 أكملت 5 جولات! +50 نقطة", embed=None, view=None)
            await interaction.response.edit_message(embed=self.make_embed(), view=self)
        else:
            reward = self.round * 5
            await db.add_points(self.author_id, self.guild_id, "اعلى_او_اقل", reward)
            await interaction.response.edit_message(content=f"❌ غل
