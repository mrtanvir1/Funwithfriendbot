import os
from urllib.parse import quote

import telebot
from telebot import types
from flask import Flask, request, abort

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
RENDER_EXTERNAL_URL = os.environ["RENDER_EXTERNAL_URL"].rstrip("/")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)
submitted_links = []

def is_admin(message):
    return message.from_user and message.from_user.id == ADMIN_USER_ID

def is_tiktok_url(text):
    if not text:
        return False
    text = text.strip()
    return text.startswith(("https://www.tiktok.com/", "https://tiktok.com/",
                            "https://vm.tiktok.com/", "https://vt.tiktok.com/"))

@bot.message_handler(commands=["start", "help"])
def start(message):
    if not is_admin(message):
        bot.reply_to(message, "এই বটটি ব্যক্তিগতভাবে ব্যবহারের জন্য সীমাবদ্ধ।")
        return
    bot.reply_to(
        message,
        "👋 <b>FunWithFriend</b> চালু হয়েছে!\n\n"
        "একটি TikTok ভিডিওর লিংক পাঠাও। আমি সেটি শেয়ার করার লিংক তৈরি করে দেব।\n\n"
        "/stats — জমা দেওয়া লিংকের সংখ্যা\n"
        "/help — সাহায্য"
    )

@bot.message_handler(commands=["stats"])
def stats(message):
    if not is_admin(message):
        return
    bot.reply_to(message, f"এখন পর্যন্ত এই চালু সেশনে জমা দেওয়া লিংক: {len(submitted_links)}")

@bot.message_handler(func=lambda m: bool(m.text))
def handle_link(message):
    if not is_admin(message):
        bot.reply_to(message, "⛔ অনুমতি নেই।")
        return
    url = message.text.strip()
    if not is_tiktok_url(url):
        bot.reply_to(message, "একটি বৈধ TikTok ভিডিও লিংক পাঠাও।")
        return

    submitted_links.append(url)
    share_url = "https://t.me/share/url?url=" + quote(url, safe="")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("বন্ধুদের সাথে শেয়ার", url=share_url))
    bot.reply_to(
        message,
        "✅ <b>ভিডিও লিংক গ্রহণ করা হয়েছে।</b>\n\n"
        "নিচের বাটনে চাপ দিয়ে Telegram-এ বন্ধুদের সাথে শেয়ার করতে পারো।\n"
        "এই বট কৃত্রিম লাইক/ভিউ তৈরি করে না; প্রকৃত দর্শকের কাছে শেয়ার করতে সাহায্য করে।",
        reply_markup=markup
    )

@app.get("/")
def health():
    return "FunWithFriend is running", 200

@app.post("/telegram/" + WEBHOOK_SECRET)
def telegram_webhook():
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        abort(403)
    update = telebot.types.Update.de_json(request.get_json(force=True))
    bot.process_new_updates([update])
    return "OK", 200

# Configure Telegram to deliver updates to this Render web service.
bot.set_webhook(
    url=f"{RENDER_EXTERNAL_URL}/telegram/{WEBHOOK_SECRET}",
    drop_pending_updates=True
)
