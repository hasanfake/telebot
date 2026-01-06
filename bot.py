import telebot
import json
from datetime import datetime, time, date

TOKEN = "8540970702:AAGtV8urV50jzTkZh-bSq_PTMnj3UFL3jGs"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

WORK_START = time(8, 0)
WORK_END = time(16, 0)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@bot.message_handler(commands=['start'])
def start(msg):
    data = load_data()
    uid = str(msg.chat.id)
    if uid not in data:
        data[uid] = {}
        save_data(data)
    bot.send_message(msg.chat.id, "✅ البوت جاهز لتسجيل الدوام")

@bot.message_handler(func=lambda m: m.text in ["دخول", "خروج", "تقرير"])
def handle(msg):
    uid = str(msg.chat.id)
    today = date.today().isoformat()
    now = datetime.now()

    # الجمعة إجازة
    if now.weekday() == 4:
        bot.send_message(msg.chat.id, "📛 اليوم جمعة (إجازة)")
        return

    data = load_data()
    user = data.setdefault(uid, {})
    day = user.setdefault(today, {"in": None, "out": None, "loss": 0})

    # تسجيل دخول
    if msg.text == "دخول":
        if now.time() <= WORK_START:
            day["in"] = WORK_START.isoformat()
            bot.send_message(msg.chat.id, "🟢 تم تسجيل الدخول (بدون تأخير)")
        else:
            delay = int((datetime.combine(date.today(), now.time()) -
                         datetime.combine(date.today(), WORK_START)).seconds / 60)
            day["loss"] += delay
            day["in"] = now.time().isoformat()
            bot.send_message(msg.chat.id, f"🟠 تأخير {delay} دقيقة")

    # تسجيل خروج
    elif msg.text == "خروج":
        if now.time() < WORK_END:
            early = int((datetime.combine(date.today(), WORK_END) -
                         datetime.combine(date.today(), now.time())).seconds / 60)
            if early >= 60:
                day["loss"] += early
                bot.send_message(msg.chat.id, f"🔴 خروج مبكر {early} دقيقة")
            else:
                bot.send_message(msg.chat.id, "🟢 خروج مقبول (أقل من ساعة)")
        else:
            bot.send_message(msg.chat.id, "🟢 خروج بنهاية الدوام")
        day["out"] = now.time().isoformat()

    # تقرير شهري
    elif msg.text == "تقرير":
        month = date.today().isoformat()[:7]
        total = 0
        for d in user:
            if d.startswith(month):
                total += user[d]["loss"]
        bot.send_message(msg.chat.id, f"📊 مجموع الدقائق الضائعة هذا الشهر: {total}")

    save_data(data)

bot.infinity_polling()
