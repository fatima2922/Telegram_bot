
import telebot

TOKEN = '7327221186:AAHrvifa6b9-oirzooxDFC-RkqWnUwbSESk'
bot = telebot.TeleBot(TOKEN)

users = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {'points': 10}
        bot.send_message(user_id, "مرحباً بك! حصلت على 10 نقاط ترحيبية 🎉")
    else:
        bot.send_message(user_id, "أنت بالفعل مسجل 💫")

@bot.message_handler(commands=['mypoints'])
def show_points(message):
    user_id = message.from_user.id
    points = users.get(user_id, {}).get('points', 0)
    bot.send_message(user_id, f"نقاطك الحالية: {points} ⭐")

bot.polling()
