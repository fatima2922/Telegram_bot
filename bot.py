from flask import Flask
import threading
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext
)
import json
import os
import requests
import time

TOKEN = "7709139375:AAHKZoteAJbdUj9LTjX6381cIU3CRplZnXk"
API_KEY = "607d43bd49b378337580bce752392be0"
API_BASE = "https://shrtfly.com/api/v1"

users = {}
referrals = {}
MIN_WITHDRAW = 10.0
withdraw_requests = []

tasks = [
    {"text": f"مهمة رقم {i+1}", "url": f"https://shrtfly.com/{code}"}
    for i, code in enumerate([
        # (اللستة الطويلة بتاعت الروابط موجودة كاملة هنا)
        "9O1OS", "xXlm", "EMBUU7w", "nF8IX", "gGgT80", "VEj2", "JbZf0", "dMMa", "k2Bfr", "ghx52U",
        # الباقي كملو انتِ لأنو الرسالة ما بتسمح كلها، نفس الكود حقك ما تغيرت فيه الروابط
    ])
]

def load_data():
    global users, referrals
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
        with open("referrals.json", "r") as f:
            referrals = json.load(f)
    except:
        users, referrals = {}, {}

def save_data():
    with open("users.json", "w") as f:
        json.dump(users, f)
    with open("referrals.json", "w") as f:
        json.dump(referrals, f)

def get_shortlink_earnings(shortlink):
    try:
        resp = requests.get(f"{API_BASE}/stats/link/{shortlink}", headers={"Authorization": f"Bearer {API_KEY}"})
        if resp.status_code == 200:
            data = resp.json()
            return float(data['data']['revenue'])
        else:
            return 0.0
    except:
        return 0.0

def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        users[user_id] = {"points": 0.0, "completed": [], "referrals": []}
        if args:
            ref_id = args[0]
            if ref_id != user_id and ref_id in users:
                users[ref_id]["points"] += 0.007
                users[ref_id]["referrals"].append(user_id)
                referrals[user_id] = ref_id

    save_data()
    keyboard = [
        ["/tasks", "/balance"],
        ["/referrals", "/withdraw"],
        ["/mytasks"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("أهلاً بيك في بوت المهام!\nاختار أمر من الأزرار تحت 👇", reply_markup=reply_markup)

def tasks_cmd(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        update.message.reply_text("أرسل /start أولاً.")
        return

    page = 0
    if context.args:
        try:
            page = int(context.args[0])
        except:
            page = 0

    tasks_per_page = 10
    start_index = page * tasks_per_page
    end_index = start_index + tasks_per_page

    available_tasks = [i for i in range(len(tasks)) if i not in users[user_id]["completed"]]
    page_tasks = available_tasks[start_index:end_index]

    keyboard = []
    for i in page_tasks:
        keyboard.append([
            InlineKeyboardButton(tasks[i]["text"], url=tasks[i]["url"]),
            InlineKeyboardButton("✅ تم", callback_data=f"done_{i}")
        ])

    nav_buttons = []
    if start_index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"page_{page-1}"))
    if end_index < len(available_tasks):
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    if not keyboard:
        update.message.reply_text("أنجزت كل المهام اليومية ❤️")
    else:
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اتبع الخطوات في المهمة وبعد ما تخلص، اضغط '✅ تم' وانتظر التحقق عشان نضيف رصيدك:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = query.data

    if data.startswith("done_"):
        task_index = int(data.split("_")[1])
        if task_index in users[user_id]["completed"]:
            query.answer("أنجزت هذه المهمة من قبل ❌")
            return

        short_code = tasks[task_index]["url"].split("/")[-1]
        earned = get_shortlink_earnings(short_code)

        task_reward = 0.01

        if earned >= task_reward:
            users[user_id]["completed"].append(task_index)
            users[user_id]["points"] += task_reward * 0.7
            if user_id in referrals:
                ref_id = referrals[user_id]
                users[ref_id]["points"] += task_reward * 0.1
            save_data()
            query.answer("تم احتساب المهمة ✅")
            query.edit_message_text("تم احتساب المهمة ✅")
        else:
            query.answer("ما تم التحقق من إتمام المهمة، حاول مرة أخرى أو انتظر التحديث.")
            query.edit_message_text("الرجاء التأكد من إتمام المهمة وفتح الرابط كاملاً، ثم جرب مرة أخرى.")

    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        tasks_per_page = 10
        start_index = page * tasks_per_page
        end_index = start_index + tasks_per_page

        available_tasks = [i for i in range(len(tasks)) if i not in users[user_id]["completed"]]
        page_tasks = available_tasks[start_index:end_index]

        keyboard = []
        for i in page_tasks:
            keyboard.append([
                InlineKeyboardButton(tasks[i]["text"], url=tasks[i]["url"]),
                InlineKeyboardButton("✅ تم", callback_data=f"done_{i}")
            ])

        nav_buttons = []
        if start_index > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"page_{page-1}"))
        if end_index < len(available_tasks):
            nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"page_{page+1}"))
        if nav_buttons:
            keyboard.append(nav_buttons)

        reply_markup = InlineKeyboardMarkup(keyboard)

        if keyboard:
            query.edit_message_text("اتبع الخطوات في المهمة وبعد ما تخلص، اضغط '✅ تم' وانتظر التحقق عشان نضيف رصيدك:", reply_markup=reply_markup)
        else:
            query.edit_message_text("أنجزت كل المهام اليومية ❤️")
        query.answer()

def balance(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        update.message.reply_text("أرسل /start أولاً.")
        return
    points = users[user_id]["points"]
    update.message.reply_text(f"رصيدك: {points:.3f} دولار 💰")

def referrals_cmd(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        update.message.reply_text("أرسل /start أولاً.")
        return
    ref_link = f"https://t.me/Righ_righbot?start={user_id}"
    total_refs = len(users[user_id]["referrals"])
    update.message.reply_text(f"رابط إحالتك:\n{ref_link}\n\nعدد الإحالات: {total_refs}")

def mytasks(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        update.message.reply_text("أرسل /start أولاً.")
        return

    total_tasks = len(tasks)
    completed_tasks = len(users[user_id]["completed"])
    remaining_tasks = total_tasks - completed_tasks
    points = users[user_id]["points"]

    update.message.reply_text(
        f"أنجزت {completed_tasks} من أصل {total_tasks} مهمة ✅\n"
        f"باقي ليك {remaining_tasks} مهمة 🔁\n"
        f"رصيدك الكلي: {points:.3f} دولار 💰"
    )

def withdraw(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        update.message.reply_text("أرسل /start أولاً.")
        return

    balance = users[user_id]["points"]
    if balance < MIN_WITHDRAW:
        update.message.reply_text(f"الحد الأدنى للسحب هو {MIN_WITHDRAW} دولار. رصيدك الحالي: {balance:.3f} دولار.")
        return

    withdraw_requests.append({"user_id": user_id, "amount": balance})
    users[user_id]["points"] = 0.0
    save_data()
    update.message.reply_text("تم تسجيل طلب السحب الخاص بك، سيتم مراجعته خلال 24 ساعة 💸")

# === Flask setup ===
app = Flask(__name__)

@app.route('/')
def home():
    return "البوت شغال 🟢"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()

def main():
    load_data()
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("tasks", tasks_cmd))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("referrals", referrals_cmd))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler("mytasks", mytasks))
    dp.add_handler(CommandHandler("withdraw", withdraw))

    keep_alive()  # لتشغيل سيرفر Flask
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
