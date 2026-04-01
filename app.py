import os
import sys

# ========= AUTO INSTALL =========
os.system(f"{sys.executable} -m pip install --upgrade pip")
os.system(f"{sys.executable} -m pip install playwright python-telegram-bot==20.7")

# ========= INSTALL BROWSER (FIXED) =========
os.system(f"{sys.executable} -m playwright install chromium")

# ========= IMPORTS =========
import time
import random
import threading
import asyncio

from playwright.sync_api import sync_playwright

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ========= CONFIG =========
BOT_TOKEN = "8728250390:AAGaSCS9EykApYCzeQMT0k4PcTsA8xj-hD4"
ADMIN_ID = 1770697159

LOGIN_URL = "https://jaiclub04.com/#/login"
USERNAME = "9351108392"
PASSWORD = "piyush1234"
# ==========================

channels = set()
history = []
last_prediction = None
last_period = None
running = False

# ========= PLAYWRIGHT =========
playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=True)
page = browser.new_page()

# ========= LOGIN =========
def login():
    page.goto(LOGIN_URL)
    page.wait_for_timeout(5000)

    page.fill("input[type='text']", USERNAME)
    page.fill("input[type='password']", PASSWORD)
    page.click("button")

    page.wait_for_timeout(8000)

# ========= POPUPS =========
def close_popups():
    page.wait_for_timeout(5000)
    try:
        page.locator("text=Confirm").click(timeout=3000)
        page.wait_for_timeout(2000)
        page.locator("text=Confirm").click(timeout=3000)
        page.wait_for_timeout(2000)
        page.locator("text=X").click(timeout=3000)
    except:
        pass

# ========= NAVIGATION =========
def open_wingo():
    page.wait_for_timeout(5000)

    page.mouse.wheel(0, 1000)
    page.wait_for_timeout(2000)

    page.locator("text=WinGo").click()
    page.wait_for_timeout(5000)

    page.locator("text=WinGo 1 Min").click()
    page.wait_for_timeout(5000)

    page.locator("text=Game history").click()
    page.wait_for_timeout(3000)

# ========= DATA =========
def get_result():
    try:
        rows = page.locator("table tr").all()
        if len(rows) > 1:
            cols = rows[1].locator("td").all()

            period = cols[0].inner_text()
            number = cols[1].inner_text()

            num = int(number)
            result = "BIG" if num >= 5 else "SMALL"

            return period, result
    except:
        return None, None

# ========= PREDICTION =========
def predict():
    if len(history) >= 3 and history[-1] == history[-2] == history[-3]:
        return "SMALL" if history[-1] == "BIG" else "BIG"
    return random.choice(["BIG", "SMALL"])

# ========= SEND =========
async def send_all(context, msg):
    for ch in channels:
        try:
            await context.bot.send_message(chat_id=ch, text=msg)
        except:
            pass

# ========= BOT LOOP =========
def run_bot(app):
    global last_prediction, last_period, running

    login()
    close_popups()
    open_wingo()

    while running:
        period, result = get_result()

        if period and period != last_period:
            history.append(result)

            if last_prediction:
                status = "WIN ✅" if last_prediction == result else "LOSS ❌"
                asyncio.run(send_all(app, f"🎯 Period: {period}\nResult: {result}\nStatus: {status}"))

            next_period = str(int(period) + 1)

            prediction = predict()
            last_prediction = prediction
            last_period = period

            asyncio.run(send_all(app, f"🔮 Next Period: {next_period}\nPrediction: {prediction}"))

        time.sleep(5)

# ========= TELEGRAM =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Add Channel", callback_data="add")],
        [InlineKeyboardButton("➖ Remove Channel", callback_data="remove")],
        [InlineKeyboardButton("▶️ Start Bot", callback_data="startbot")],
        [InlineKeyboardButton("⏹ Stop Bot", callback_data="stopbot")],
    ]

    await update.message.reply_text("🔥 CONTROL PANEL", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "add":
        await query.message.reply_text("👉 Channel me /addchannel likho")

    elif query.data == "remove":
        keyboard = [[InlineKeyboardButton(str(ch), callback_data=f"del_{ch}")] for ch in channels]
        await query.message.reply_text("Select channel:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("del_"):
        ch_id = int(query.data.split("_")[1])
        channels.discard(ch_id)
        await query.message.reply_text(f"❌ Removed {ch_id}")

    elif query.data == "startbot":
        if not running:
            running = True
            threading.Thread(target=run_bot, args=(context.application,)).start()
            await query.message.reply_text("🚀 Bot Started")

    elif query.data == "stopbot":
        running = False
        await query.message.reply_text("⏹ Bot Stopped")

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    chat_id = update.effective_chat.id

    if str(chat_id).startswith("-100"):
        channels.add(chat_id)
        await update.message.reply_text("✅ Channel Added")

# ========= MAIN =========
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addchannel", add_channel))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()