# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import random
import os

# ---------------- إعدادات أساسية ----------------
DISCORD_TOKEN = "ضع_هنا_توكن_البوت"  # ضع توكن البوت هنا
QUIZ_TIMEOUT = 30
POINTS = {"Easy": 5, "Medium": 10, "Hard": 15}
CATEGORIES = ["أنمي", "Free Fire", "Gaming", "عامة"]

DATA_FILE = "scores.json"
HISTORY_FILE = "history.json"

# ---------------- إدارة النقاط ----------------
def load_scores():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        return json.load(open(DATA_FILE,"r",encoding="utf-8"))
    except:
        return {}

def save_scores(scores):
    json.dump(scores, open(DATA_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def add_points(uid, pts):
    scores = load_scores()
    scores[str(uid)] = scores.get(str(uid), 0) + pts
    save_scores(scores)

def top_scores(n=10):
    items = [(int(uid), pts) for uid, pts in load_scores().items()]
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:n]

# ---------------- إدارة السجل ----------------
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        return json.load(open(HISTORY_FILE,"r",encoding="utf-8"))
    except:
        return {}

def save_history(history):
    json.dump(history, open(HISTORY_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def record_answer(user_id, question, answer, correct, category, difficulty):
    history = load_history()
    user_history = history.get(str(user_id), [])
    user_history.append({
        "سؤال": question,
        "إجابة": answer,
        "صح": correct,
        "فئة": category,
        "صعوبة": difficulty
    })
    history[str(user_id)] = user_history
    save_history(history)

# ---------------- Buttons ----------------
class ChoiceView(discord.ui.View):
    def __init__(self, choices, correct):
        super().__init__(timeout=QUIZ_TIMEOUT)
        self.correct = correct
        self.answered = False
        self.result = False
        for i, c in enumerate(choices):
            self.add_item(ChoiceButton(label=c, i=i))

class ChoiceButton(discord.ui.Button):
    def __init__(self, label, i):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.i = i
    async def callback(self, interaction: discord.Interaction):
        view: ChoiceView = self.view
        if view.answered:
            await interaction.response.send_message("❌ تمّت الإجابة مسبقاً!", ephemeral=True)
            return
        view.answered = True
        view.result = self.i == view.correct
        for item in view.children:
            item.disabled = True
        await interaction.response.edit_message(view=view)

# ---------------- Intents ----------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ {bot.user} جاهز ويشتغل! {len(synced)} أوامر مسجلة")
    except Exception as e:
        print(e)

# ---------------- مكتبة أسئلة ثابتة ----------------
# ملاحظة: هذا مثال صغير، يمكن استبداله بآلاف الأسئلة لاحقًا
LIBRARY = {
    "أنمي": [
        {"نص":"من هو بطل ون بيس؟","خيارات":["لوفي","زورو","ناروتو","غوكو"],"صح":0,"صعوبة":"Easy"},
        {"نص":"من قاتل في القوس الأول؟","خيارات":["لور","كيز","أوكي","ليو"],"صح":1,"صعوبة":"Medium"}
    ],
    "Free Fire": [
        {"نص":"أفضل لاعب Free Fire في العالم؟","خيارات":["أ","ب","ج","د"],"صح":0,"صعوبة":"Easy"},
        {"نص":"أي سلاح أقوى؟","خيارات":["AK","M4","UMP","MP5"],"صح":1,"صعوبة":"Hard"}
    ],
    "Gaming": [
        {"نص":"أكثر لعبة مبيعًا؟","خيارات":["Minecraft","Fortnite","GTA","CS"],"صح":0,"صعوبة":"Easy"}
    ],
    "عامة": [
        {"نص":"عاصمة فرنسا؟","خيارات":["باريس","لندن","مدريد","روما"],"صح":0,"صعوبة":"Easy"}
    ]
}

def get_questions(user_id, category, difficulty, number):
    history = load_history()
    answered = [h["سؤال"] for h in history.get(str(user_id),[])]
    pool = [q for q in LIBRARY[category] if q["صعوبة"]==difficulty and q["نص"] not in answered]
    if len(pool)<number: number = len(pool)
    return random.sample(pool, number)

# ---------------- أوامر ----------------
@bot.tree.command(name="لوحة_النتائج", description="عرض أفضل اللاعبين")
async def leaderboard(inter: discord.Interaction):
    scores = top_scores(10)
    if not scores:
        await inter.response.send_message("لا توجد نتائج بعد!")
        return
    embed = discord.Embed(title="🏆 لوحة النتائج", color=discord.Color.green())
    for i, (uid, pts) in enumerate(scores,1):
        user = await bot.fetch_user(uid)
        embed.add_field(name=f"{i}. {user.name}", value=f"النقاط: {pts}", inline=False)
    await inter.response.send_message(embed=embed)

@bot.tree.command(name="سجل", description="عرض سجل إجاباتك")
async def show_history(inter: discord.Interaction):
    history = load_history().get(str(inter.user.id), [])
    if not history:
        await inter.response.send_message("❌ لم يتم إيجاد سجل لك.")
        return
    embed = discord.Embed(title=f"📝 سجل {inter.user.name}", color=discord.Color.blue())
    for h in history[-10:]:
        embed.add_field(name=h["سؤال"], value=f"إجابتك: {h['إجابة']} - صح: {h['صح']}", inline=False)
    await inter.response.send_message(embed=embed)

@bot.tree.command(name="مسابقة", description="ابدأ مسابقة")
@app_commands.choices(
    فئة=[app_commands.Choice(name=c, value=c) for c in CATEGORIES]
)
@app_commands.choices(
    صعوبة=[app_commands.Choice(name=s, value=s) for s in POINTS.keys()]
)
async def quiz(inter: discord.Interaction, فئة: app_commands.Choice[str], صعوبة: app_commands.Choice[str], عدد: int=5):
    await inter.response.defer(thinking=True)
    questions_pool = get_questions(inter.user.id, فئة.value, صعوبة.value, عدد)
    if not questions_pool:
        await inter.followup.send("❌ لا توجد أسئلة متاحة لهذه الفئة والصعوبة.")
        return
    total_points = 0
    for q in questions_pool:
        view = ChoiceView(q["خيارات"], q["صح"])
        msg = await inter.followup.send(f"❓ {q['نص']}", view=view)
        waited = 0
        while not view.answered and waited < QUIZ_TIMEOUT:
            await asyncio.sleep(0.5)
            waited += 0.5
        if not view.answered:
            record_answer(inter.user.id, q["نص"], "لا إجابة", False, فئة.value, صعوبة.value)
            await inter.followup.send(f"⏰ انتهى الوقت للسؤال: {q['نص']}")
            break
        answer_text = q["خيارات"][view.correct] if view.result else "خاطئة"
        record_answer(inter.user.id, q["نص"], answer_text, view.result, فئة.value, صعوبة.value)
        if view.result:
            pts = POINTS.get(q.get("صعوبة", صعوبة.value), 5)
            total_points += pts
            add_points(inter.user.id, pts)
        else:
            await inter.followup.send(f"❌ إجابة خاطئة! المسابقة انتهت.\nمجموع نقاطك: {total_points}")
            break
    embed = discord.Embed(title="🎉 لقد أنهيت المسابقة!", description=f"{inter.user.mention} حصل على {total_points} نقاط", color=discord.Color.gold())
    if inter.user.avatar:
        embed.set_thumbnail(url=inter.user.avatar.url)
    await inter.followup.send(embed=embed)

# ---------------- تشغيل البوت ----------------
if __name__=="__main__":
    bot.run(DISCORD_TOKEN)
