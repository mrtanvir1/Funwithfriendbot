import os
import time
import hmac
import logging
from urllib.parse import quote, urlparse

import telebot
from telebot import types, apihelper
from flask import Flask, request, abort, jsonify

# ==================================
# CONFIGURATION
# ==================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
RENDER_EXTERNAL_URL = os.environ["RENDER_EXTERNAL_URL"].rstrip("/")

if not WEBHOOK_SECRET or len(WEBHOOK_SECRET) > 256:
    raise ValueError("Invalid WEBHOOK_SECRET")

# Telegram API timeout settings
apihelper.CONNECT_TIMEOUT = 20
apihelper.READ_TIMEOUT = 60

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# Bot and Flask
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# Session storage
submitted_links = []

# Webhook paths
WEBHOOK_PATH = f"/telegram/{WEBHOOK_SECRET}"
SETUP_PATH = f"/setup-webhook/{WEBHOOK_SECRET}"


# ==================================
# HELPER FUNCTIONS
# ==================================

def is_admin(message):
    return bool(
        message.from_user
        and message.from_user.id == ADMIN_USER_ID
    )


def is_tiktok_url(text):
    if not text:
        return False

    try:
        parsed = urlparse(text.strip())

        allowed_hosts = {
            "tiktok.com",
            "www.tiktok.com",
            "vm.tiktok.com",
            "vt.tiktok.com",
            "m.tiktok.com"
        }

        return (
            parsed.scheme == "https"
            and parsed.hostname in allowed_hosts
        )

    except Exception:
        return False


# ==================================
# START COMMAND
# ==================================

@bot.message_handler(commands=["start", "help"])
def start(message):

    if not is_admin(message):
        bot.reply_to(
            message,
            "⛔ এই বটটি ব্যক্তিগত ব্যবহারের জন্য সীমাবদ্ধ।"
        )
        return

    bot.reply_to(
        message,
        "👋 <b>FunWithFriend</b> চালু হয়েছে!\n\n"
        "একটি TikTok ভিডিওর লিংক পাঠাও। "
        "আমি সেটি বন্ধুদের সঙ্গে শেয়ার করার লিংক তৈরি করে দেব।\n\n"
        "📊 /stats — জমা দেওয়া লিংকের সংখ্যা\n"
        "❓ /help — সাহায্য"
    )


# ==================================
# STATS COMMAND
# ==================================

@bot.message_handler(commands=["stats"])
def stats(message):

    if not is_admin(message):
        return

    bot.reply_to(
        message,
        f"📊 এই চালু সেশনে জমা দেওয়া লিংক: "
        f"<b>{len(submitted_links)}</b>"
    )


# ==================================
# TIKTOK LINK HANDLER
# ==================================

@bot.message_handler(func=lambda message: bool(message.text))
def handle_link(message):

    if not is_admin(message):
        return

    url = message.text.strip()

    if not is_tiktok_url(url):
        bot.reply_to(
            message,
            "⚠️ একটি বৈধ TikTok ভিডিও লিংক পাঠাও।"
        )
        return

    submitted_links.append(url)

    share_url = (
        "https://t.me/share/url?url="
        + quote(url, safe="")
    )

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "বন্ধুদের সাথে শেয়ার",
            url=share_url
        )
    )

    bot.reply_to(
        message,
        "✅ <b>ভিডিও লিংক গ্রহণ করা হয়েছে!</b>\n\n"
        "নিচের বাটনে চাপ দিয়ে Telegram-এ বন্ধুদের সঙ্গে "
        "ভিডিও লিংক শেয়ার করতে পারো।\n\n"
        "ℹ️ এই বট কৃত্রিম লাইক বা ভিউ তৈরি করে না।",
        reply_markup=markup
    )


# ==================================
# HEALTH CHECK
# ==================================

@app.get("/")
@app.get("/healthz")
def health():

    return jsonify({
        "status": "running",
        "bot": "FunWithFriend",
        "message": "Service is healthy"
    }), 200


# ==================================
# WEBHOOK SETUP WITH RETRY
# ==================================

@app.get(SETUP_PATH)
def setup_webhook():

    webhook_url = (
        f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"
    )

    last_error = None

    for attempt in range(1, 4):

        try:

            logger.info(
                "Webhook setup attempt %s/3",
                attempt
            )

            ok = bot.set_webhook(
                url=webhook_url,
                secret_token=WEBHOOK_SECRET,
                drop_pending_updates=False
            )

            if ok:

                logger.info("Webhook configured successfully")

                return jsonify({
                    "ok": True,
                    "message": "Webhook configured successfully."
                }), 200

            last_error = "Telegram did not confirm webhook setup"

        except Exception as exc:

            last_error = type(exc).__name__

            logger.warning(
                "Webhook setup failed on attempt %s: %s",
                attempt,
                last_error
            )

        if attempt < 3:
            time.sleep(attempt * 5)

    logger.error(
        "Webhook setup failed after 3 attempts: %s",
        last_error
    )

    return jsonify({
        "ok": False,
        "error": last_error,
        "message": (
            "Webhook setup failed. "
            "Please check Render logs and try again later."
        )
    }), 502


# ==================================
# TELEGRAM WEBHOOK RECEIVER
# ==================================

@app.post(WEBHOOK_PATH)
def telegram_webhook():

    # Verify Telegram secret header
    telegram_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token",
        ""
    )

    if not hmac.compare_digest(
        telegram_secret,
        WEBHOOK_SECRET
    ):
        abort(403)

    # Verify content type
    if request.headers.get(
        "content-type", ""
    ).split(";")[0] != "application/json":

        abort(403)

    # Read Telegram update
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(400)

    try:

        update = telebot.types.Update.de_json(data)

        bot.process_new_updates([update])

        return "OK", 200

    except Exception:

        logger.exception("Error processing Telegram update")

        return "Internal Server Error", 500


# ==================================
# APPLICATION START
# ==================================

# IMPORTANT:
# Do not call set_webhook() here.
# Render/Gunicorn may import this file multiple times.

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
