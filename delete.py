import sqlite3
import json
import time
import threading
import urllib.request
import urllib.parse
import random
from datetime import datetime, date
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ======================= PREMIUM EMOJIS =======================
def ce(name):
    if name in EMOJIS:
        emoji, emoji_id = EMOJIS[name]
        return f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>'
    return "✨"
    
EMOJIS = {
    "success": ("✅", "5316827280863934685"),
    "danger": ("❌", "4958526153955476488"),
    "warning": ("⚠️", "5447644880824181073"),
    "rocket": ("🚀", "5316571734604790521"),
    "money": ("💰", "6089104607328342288"),
    "profile": ("👤", "5316992572680320646"),
    "shop": ("🛒", "5226656353744862682"),
    "shield": ("🛡️", "5316827280863934685"),
    "fire": ("🔥", "5447644880824181073"),
    "apple": ("🍎", "5226656353744862682"),
    "name_icon": ("🆔", "5316992572680320646"),
    "mobile": ("📱", "5316571734604790521"),
    "pencil": ("✏️", "5447644880824181073"),
    "fail": ("🚫", "4958526153955476488"),
}

# ======================= CONFIG =======================
BOT_TOKEN = "8610622953:AAHWGyMq60inMKwI7s25bL0A3dZmyX6m8N0"
ADMIN_USER_ID = 8417161342
SUCCESS_IMG = "https://t.me/c/2387714877/2363"
API_KEY = "fmpay_27518ff39143b30ed4cf1fa6ca6868e72cfa4a99"
UPI_ID = "ownerhimanshu@fam"

DB_PATH = "Abhinav_Dad.db"

# Constants for Emojis used in show_products/plans
PREMIUM_DIAMOND = "💎"
PREMIUM_LIGHTNING = "⚡"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            days INTEGER NOT NULL,
            price INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS license_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            license_key TEXT NOT NULL UNIQUE,
            used INTEGER DEFAULT 0,
            used_by INTEGER DEFAULT NULL,
            used_at TIMESTAMP NULL DEFAULT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            spin_count INTEGER DEFAULT 0,
            last_spin_date TEXT DEFAULT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified INTEGER DEFAULT 0,
            phone_number TEXT DEFAULT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT DEFAULT 'purchase',
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at INTEGER NOT NULL
        )
    """)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT DEFAULT NULL")
    except:
        pass
    conn.commit()
    cursor.close()
    conn.close()

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, json=data, timeout=10)
    except:
        pass

def check_payments():
    while True:
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pending_payments WHERE status='pending'")
            rows = cursor.fetchall()
            now = time.time()
            for row in rows:
                uid = row[1]
                order_id = row[2]
                amount = row[3]
                created_at = row[5]
                if now - created_at > 600:
                    cursor.execute("UPDATE pending_payments SET status='failed' WHERE id=?", (row[0],))
                    conn.commit()
                    send_telegram_message(uid, "⌛ Payment expired (10 minutes). Please try again.")
                    continue
                verify_url = f"https://fampay.anujbots.xyz/verify.php?order_id={order_id}&api_key={API_KEY}"
                try:
                    req = urllib.request.Request(verify_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as response:
                        raw = response.read().decode()
                    res = json.loads(raw)
                    status = str(res.get("status", "")).lower()
                    if status == "success":
                        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
                        urow = cursor.fetchone()
                        new_bal = (urow[0] if urow else 0) + amount
                        if not urow:
                            cursor.execute("INSERT INTO users (id, balance) VALUES (?,?)", (uid, amount))
                        else:
                            cursor.execute("UPDATE users SET balance=? WHERE id=?", (new_bal, uid))
                        cursor.execute("INSERT INTO transactions (user_id, amount, type) VALUES (?,?,'add_money')", (uid, amount))
                        cursor.execute("UPDATE pending_payments SET status='success' WHERE id=?", (row[0],))
                        conn.commit()
                        send_telegram_message(uid, f"✅ Payment Successful!\n💰 ₹{amount} added\n💵 New Balance: ₹{new_bal}")
                        send_telegram_message(ADMIN_USER_ID, f"💰 Payment received from user {uid}\nAmount: ₹{amount}")
                    elif status == "failed":
                        cursor.execute("UPDATE pending_payments SET status='failed' WHERE id=?", (row[0],))
                        conn.commit()
                        send_telegram_message(uid, "❌ Payment Failed. Please try again or contact support.")
                except Exception as e:
                    print(f"Verify error: {e}")
            cursor.close()
            conn.close()
        except Exception as e:
            print("Payment thread error:", e)
        time.sleep(2)

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, parse_mode="HTML")
user_states = {}

def is_verified(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT verified FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row and row[0] == 1

def set_verified(user_id, phone_number):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET verified=1, phone_number=? WHERE id=?", (phone_number, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def is_banned(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT banned FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row and row[0] == 1

def ban_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned=1 WHERE id=?", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

def unban_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned=0 WHERE id=?", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

def can_spin(user_id):
    today = date.today().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT spin_count, last_spin_date FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return True, 1, today
    spin_count = row[0] or 0
    last_date = row[1]
    if last_date != today:
        cursor.execute("UPDATE users SET spin_count=0, last_spin_date=? WHERE id=?", (today, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True, 1, today
    remaining = 1 - spin_count
    cursor.close()
    conn.close()
    return remaining > 0, remaining, today

def record_spin(user_id, amount):
    today = date.today().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, spin_count, last_spin_date) VALUES (?,0,?)", (user_id, today))
    cursor.execute("UPDATE users SET spin_count = spin_count + 1, last_spin_date = ? WHERE id = ?", (today, user_id))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, details) VALUES (?,?,'spin',?)", (user_id, amount, f"Lucky spin won ₹{amount}"))
    conn.commit()
    cursor.close()
    conn.close()

MAIN_MENU_TEXT = f"""╔═══━━━── • ──━━━═══╗

{ce("rocket")} <b>VIVEK PANEL STORE</b>

{ce("shop")} Buy Premium Products
{ce("money")} Instant Payments
{ce("success")} Auto Delivery
{ce("warning")} 24x7 Support

{ce("rocket")} Tap Below To Start Shopping
"""

def get_main_menu(user_id):
    if is_banned(user_id):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(f"{ce("mobile")} Contact Support", callback_data="support"))
        return markup

    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        [InlineKeyboardButton("Shop Now", callback_data="shop_now", icon_custom_emoji_id=EMOJIS["shop"][1], style="primary")],
        [InlineKeyboardButton("Profile", callback_data="profile", icon_custom_emoji_id=EMOJIS["profile"][1], style="primary")],
        [InlineKeyboardButton("Add Balance", callback_data="add_balance", icon_custom_emoji_id=EMOJIS["money"][1], style="primary")],
        [InlineKeyboardButton("All History", callback_data="history", icon_custom_emoji_id=EMOJIS["mobile"][1], style="primary")],
        # NEW BUTTONS: View & Delete My Data
        [InlineKeyboardButton("📋 View My Data", callback_data="view_my_data", icon_custom_emoji_id=EMOJIS["name_icon"][1], style="primary")],
        [InlineKeyboardButton("🗑️ Delete My Data", callback_data="delete_my_data", icon_custom_emoji_id=EMOJIS["fail"][1], style="danger")],
        [InlineKeyboardButton("Referral - Invite", callback_data="referral", icon_custom_emoji_id=EMOJIS["name_icon"][1], style="primary")],
        [InlineKeyboardButton("How To Buy", callback_data="tutorial", icon_custom_emoji_id=EMOJIS["shield"][1], style="primary")],
        [InlineKeyboardButton("Lucky Spin", callback_data="lucky_spin", icon_custom_emoji_id=EMOJIS["pencil"][1], style="success")],
        [InlineKeyboardButton("Support", callback_data="support", icon_custom_emoji_id=EMOJIS["pencil"][1], style="success")],
    ]
    
    for row in buttons:
        markup.row(*row)

    if is_admin(user_id):
        markup.add(InlineKeyboardButton("Admin Panel", callback_data="admin_panel",icon_custom_emoji_id=EMOJIS["profile"][1], style="danger"))

    return markup

def is_admin(user_id):
    if user_id == ADMIN_USER_ID:
        return True
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return bool(data)
        
def get_admin_panel():
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("Add Product", callback_data="admin_add_product",icon_custom_emoji_id=EMOJIS["success"][1], style="primary"),
        InlineKeyboardButton("Edit Product", callback_data="admin_edit_product",icon_custom_emoji_id=EMOJIS["pencil"][1], style="success"),
        InlineKeyboardButton("Delete Product", callback_data="admin_del_product",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger"),
        InlineKeyboardButton("Add Plan", callback_data="admin_add_plan",icon_custom_emoji_id=EMOJIS["shield"][1], style="success"),
        InlineKeyboardButton("Delete Plan", callback_data="admin_del_plan",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger"),
        InlineKeyboardButton("Add Keys", callback_data="admin_add_keys",icon_custom_emoji_id=EMOJIS["shield"][1], style="success"),
        InlineKeyboardButton("List Keys", callback_data="admin_list_keys",icon_custom_emoji_id=EMOJIS["success"][1], style="primary"),
        InlineKeyboardButton("Delete Key", callback_data="admin_del_key",icon_custom_emoji_id=EMOJIS["danger"][1], style="danger"),
        InlineKeyboardButton("Add Balance", callback_data="admin_add_balance",icon_custom_emoji_id=EMOJIS["money"][1], style="success"),
        InlineKeyboardButton("Remove Balance", callback_data="admin_remove_balance",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger"),
        InlineKeyboardButton("Ban User", callback_data="admin_ban_user",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger"),
        InlineKeyboardButton("Unban User", callback_data="admin_unban_user",icon_custom_emoji_id=EMOJIS["success"][1], style="success"),
        InlineKeyboardButton("Stats", callback_data="admin_stats",icon_custom_emoji_id=EMOJIS["pencil"][1], style="danger"),
        InlineKeyboardButton("Back to Main", callback_data="back_main",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger"),
    ]
    markup.add(*buttons)
    return markup

def send_verification_request(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = KeyboardButton("📱 Share My Number", request_contact=True)
    markup.add(btn)
    bot.send_message(
        chat_id,
        f"""{ce("mobile")} Welcome to Vivek Panel Store!\n\nTo continue, please share your phone number by tapping the button below.
        """,reply_markup=markup
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    username = message.from_user.username
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, username, balance, banned, spin_count, last_spin_date, verified) VALUES (?,?,0,0,0,?,0)", 
                   (uid, username, date.today().isoformat()))
    conn.commit()
    cursor.close()
    conn.close()

    if is_verified(uid):
        bot.send_message(message.chat.id, MAIN_MENU_TEXT, parse_mode="HTML", reply_markup=get_main_menu(uid))
    else:
        send_verification_request(message.chat.id)

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(
            message,
            f"{ce('danger')} Kisi message pe reply karke /broadcast bhejo."
        )
        return
    status_msg = bot.reply_to(
        message,
        "📢 Broadcast Started..."
    )
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    sent = 0
    failed = 0
    for user in users:
        user_id = user[0]
        try:
            bot.copy_message(
                user_id,
                message.chat.id,
                message.reply_to_message.message_id
            )
            sent += 1
            print(f"Sent to {user_id}")
        except Exception as e:
            failed += 1
            print(f"Failed {user_id} -> {e}")
    bot.edit_message_text(
        f"""
{ce('success')} Broadcast Completed

{ce('fire')} Sent: {sent}
{ce('danger')} Failed: {failed}
{ce('profile')} Total: {sent + failed}
""",
        status_msg.chat.id,
        status_msg.message_id
    )

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if message.from_user.id != ADMIN_USER_ID:
        return
    try:
        uid = int(message.text.split()[1])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
            (uid,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        bot.reply_to(
            message,
            f"✅ {uid} Added As Admin"
        )
        try:
            bot.send_message(
                uid,
                "🎉 You Got Admin Access"
            )
        except:
            pass
    except:
        bot.reply_to(
            message,
            "Usage:\n/addadmin USER_ID"
        )

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    if message.from_user.id != ADMIN_USER_ID:
        return
    try:
        uid = int(message.text.split()[1])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM admins WHERE user_id=?",
            (uid,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        bot.reply_to(
            message,
            "✅ Admin Removed"
        )
    except:
        bot.reply_to(
            message,
            "Usage:\n/removeadmin USER_ID"
        )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    contact = message.contact
    if contact and contact.user_id == user_id:
        set_verified(user_id, contact.phone_number)
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("/start"))
        bot.send_message(message.chat.id, f"""{ce("success")} Verification complete! Welcome to the store.""", reply_markup=markup)
        bot.send_message(message.chat.id, MAIN_MENU_TEXT, parse_mode="HTML", reply_markup=get_main_menu(user_id))
    else:
        bot.send_message(message.chat.id, f"{ce("mobile")} Please share your own phone number using the button.")
        send_verification_request(message.chat.id)

@bot.message_handler(func=lambda m: True)
def handle_non_contact(message):
    if not is_verified(message.from_user.id):
        send_verification_request(message.chat.id)

# ======================= NEW FUNCTIONS FOR VIEW & DELETE =======================

def view_my_data(call):
    """Display all stored data of the user."""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        bot.edit_message_text("❌ No data found for your ID.", chat_id, msg_id)
        cursor.close()
        conn.close()
        return

    # Fetch transactions (last 10)
    cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,))
    transactions = cursor.fetchall()

    # Fetch pending payments
    cursor.execute("SELECT * FROM pending_payments WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    pending = cursor.fetchall()
    cursor.close()
    conn.close()

    # Build the message
    text = f"<b>📋 Your Stored Data</b>\n\n"
    text += f"🆔 User ID: <code>{user['id']}</code>\n"
    text += f"👤 Username: @{user['username'] or 'N/A'}\n"
    text += f"💰 Balance: ₹{user['balance']}\n"
    text += f"📱 Phone: {user['phone_number'] or 'Not provided'}\n"
    text += f"✅ Verified: {'Yes' if user['verified'] else 'No'}\n"
    text += f"🎰 Spin Count (today): {user['spin_count']}\n"
    text += f"📅 Last Spin: {user['last_spin_date'] or 'Never'}\n"
    text += f"🚫 Banned: {'Yes' if user['banned'] else 'No'}\n"
    text += f"📆 Joined: {user['joined_at']}\n\n"

    if transactions:
        text += "<b>📜 Last 10 Transactions:</b>\n"
        for t in transactions:
            sign = "+" if t['type'] in ('add_money', 'spin') else "-"
            text += f"• {sign}₹{t['amount']} ({t['type']}) {t['details'] or ''} - {t['created_at']}\n"
    else:
        text += "📭 No transactions.\n"

    if pending:
        text += f"\n<b>⏳ Pending Payments:</b>\n"
        for p in pending:
            text += f"• Order {p['order_id']} - ₹{p['amount']} ({p['status']}) - {date.fromtimestamp(p['created_at'])}\n"
    else:
        text += "\n✅ No pending payments."

    # Back button
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("◀️ Back to Menu", callback_data="back_main"))
    bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML", reply_markup=markup)

def delete_my_data(call):
    """Ask for confirmation before deleting all data."""
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Yes, Delete Everything", callback_data="confirm_delete"),
        InlineKeyboardButton("❌ Cancel", callback_data="back_main")
    )
    bot.edit_message_text(
        "⚠️ <b>Are you sure you want to permanently delete ALL your data?</b>\n"
        "This includes your phone number, balance, transaction history, spin data, and pending payments.\n"
        "This action is <b>IRREVERSIBLE</b>!",
        chat_id, msg_id, parse_mode="HTML", reply_markup=markup
    )

def confirm_delete(call):
    """Actually delete the user's data from all tables."""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM pending_payments WHERE user_id = ?", (user_id,))
        conn.commit()
        bot.edit_message_text(
            f"{ce('success')} <b>Your data has been successfully deleted.</b>\n"
            "You can now use /start to register again.",
            chat_id, msg_id, parse_mode="HTML"
        )
    except Exception as e:
        conn.rollback()
        bot.edit_message_text(f"❌ Error deleting data: {e}", chat_id, msg_id)
    finally:
        cursor.close()
        conn.close()

# =====================================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    if not is_verified(user_id):
        bot.answer_callback_query(call.id, f"{ce("mobile")} Please verify your phone number first using /start", show_alert=True)
        return

    if is_banned(user_id) and call.data not in ["support", "back_main", "profile", "view_my_data", "delete_my_data"]:
        bot.answer_callback_query(call.id, f"{ce("warning")} You are banned. Contact support.", show_alert=True)
        return

    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    # ---- New cases ----
    if data == "view_my_data":
        view_my_data(call)
    elif data == "delete_my_data":
        delete_my_data(call)
    elif data == "confirm_delete":
        confirm_delete(call)
    # ---- Existing cases ----
    elif data == "shop_now":
        show_products(call)
    elif data == "profile":
        show_profile(call, user_id)
    elif data == "add_balance":
        ask_amount(call)
    elif data == "history":
        show_history(call, user_id)
    elif data == "referral":
        bot.edit_message_text(f"""{ce("rocket")} <b>Referral Program</b>\n\nInvite friends and earn ₹10 each!\nYour link: https://t.me/Itsvivekop1store_bot?start=ref""", chat_id, msg_id, parse_mode="HTML", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Back", callback_data="back_main",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger")))
    elif data == "support":
        bot.edit_message_text(f"{ce("mobile")}<b>Support</b>\n\nContact admin: @ItsVivekOP1", chat_id, msg_id, parse_mode="HTML", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Back", callback_data="back_main",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger")))
    elif data == "lucky_spin":
        allowed, remaining, _ = can_spin(user_id)
        if not allowed:
            bot.answer_callback_query(call.id, f"Daily spin limit reached (1 spins). Try tomorrow.", show_alert=True)
            return
        prize = random.randint(1, 5)
        record_spin(user_id, prize)
        remaining_spins = remaining - 1
        bot.edit_message_text(f"{ce("rocket")} <b>Lucky Spin Result</b>\n\n{ce("fire")} You won ₹{prize}!\n{ce("success")} Balance updated.\n\n{ce("name_icon")} Remaining spins today: {remaining_spins}", chat_id, msg_id, parse_mode="HTML", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Back", callback_data="back_main",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger")))
    elif data == "back_main" or data == "cancel_conv":
        bot.edit_message_text(MAIN_MENU_TEXT, chat_id, msg_id, parse_mode="HTML", reply_markup=get_main_menu(user_id))
    elif data.startswith("selectplanprod_"):
        product_id = int(data.split("_")[1])
        user_states[user_id] = {"plan_product_id": product_id}
        msg = bot.send_message(chat_id, "📅 Send:\nDays Price\n\nExample:\n30 499")
        bot.register_next_step_handler(msg, add_plan)
    elif data == "tutorial":
        bot.answer_callback_query(call.id, "🎬 Tutorial\n1. /start to see menu\n2. Shop → select product → buy\n3. Add Money via QR\n4. Spin daily to win up to ₹5", show_alert=True)
    elif data.startswith("product_"):
        product_id = int(data.split("_")[1])
        show_product_plans(call, product_id)
    elif data.startswith("buy_"):
        parts = data.split("_")
        if len(parts) == 3:
            _, product_id, plan_id = parts
            process_purchase(call, int(product_id), int(plan_id))
    elif data == "admin_panel" and is_admin(user_id):
        bot.edit_message_text("🔧 <b>Admin Panel</b>", chat_id, msg_id, parse_mode="HTML", reply_markup=get_admin_panel())
    elif data.startswith("admin_"):
        handle_admin_actions(call, data)
    elif data.startswith("editprod_"):
        prod_id = int(data.split("_")[1])
        bot.edit_message_text(f"{ce("shop")} Send new product name:", chat_id, msg_id)
        bot.register_next_step_handler(call.message, lambda m: edit_product_name(m, prod_id))
    elif data.startswith("delprod_"):
        prod_id = int(data.split("_")[1])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (prod_id,))
        conn.commit()
        cursor.close()
        conn.close()
        bot.edit_message_text(f"{ce("success")} Product deleted.", chat_id, msg_id)
    elif data.startswith("delplan_"):
        plan_id = int(data.split("_")[1])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM plans WHERE id=?", (plan_id,))
        conn.commit()
        cursor.close()
        conn.close()
        bot.edit_message_text(f"{ce("success")} Plan deleted.", chat_id, msg_id)
    elif data.startswith("addkeys_prod_"):
        prod_id = int(data.split("_")[2])
        user_states[user_id] = {"action": "add_keys_select_plan", "prod_id": prod_id}
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, days, price FROM plans WHERE product_id=?", (prod_id,))
        plans = cursor.fetchall()
        cursor.close()
        conn.close()
        if not plans:
            bot.edit_message_text(f"{ce("warning")} No plans. Add a plan first.", chat_id, msg_id)
            return
        markup = InlineKeyboardMarkup()
        for pl in plans:
            markup.add(InlineKeyboardButton(f"📆 {pl[1]} days - ₹{pl[2]}", callback_data=f"addkeys_plan_{pl[0]}"))
        markup.add(InlineKeyboardButton("◀️ Cancel", callback_data="admin_panel"))
        bot.edit_message_text(f"{ce("shop")} Select plan:", chat_id, msg_id, reply_markup=markup)
    elif data.startswith("addkeys_plan_"):
        plan_id = int(data.split("_")[2])
        user_states[user_id] = {"action": "add_keys_final", "prod_id": user_states.get(user_id, {}).get("prod_id"), "plan_id": plan_id}
        bot.edit_message_text(f"{ce("fire")} Send keys (one per line):", chat_id, msg_id)
        bot.register_next_step_handler(call.message, receive_keys)
    else:
        bot.answer_callback_query(call.id, "🔜 Feature coming soon")

# ----------------------- All other functions remain unchanged -----------------------
# (show_products, show_product_plans, process_purchase, show_profile, show_history, 
#  ask_amount, receive_amount, handle_admin_actions, add_product, edit_product_name,
#  add_plan, add_balance_admin, remove_balance_admin, ban_user_cmd, unban_user_cmd,
#  receive_keys, delete_key, list_all_keys, etc.)
# They are already defined above, I'm just keeping them as they are.

def show_products(call):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products ORDER BY id DESC")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    if not products:
        bot.edit_message_text(f"{ce("danger")} No products.", call.message.chat.id, call.message.message_id)
        return
    markup = InlineKeyboardMarkup(row_width=1)
    for p in products:
        markup.add(InlineKeyboardButton(f" {p[1]}", callback_data=f"product_{p[0]}",icon_custom_emoji_id=EMOJIS["shop"][1], style="danger"))
    markup.add(InlineKeyboardButton(" Back", callback_data="back_main",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger"))
    bot.edit_message_text("🛒 <b>Select Product:</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

def show_product_plans(call, product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, days, price FROM plans WHERE product_id=? ORDER BY days", (product_id,))
    plans = cursor.fetchall()
    cursor.execute("SELECT name FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()
    if not plans:
        bot.edit_message_text("⚠️ No plans.", call.message.chat.id, call.message.message_id)
        return
    markup = InlineKeyboardMarkup(row_width=1)
    for pl in plans:
        markup.add(InlineKeyboardButton(f" {pl[1]} Days • ₹{pl[2]}", callback_data=f"buy_{product_id}_{pl[0]}",icon_custom_emoji_id=EMOJIS["shop"][1], style="danger"))
    markup.add(InlineKeyboardButton(" Back", callback_data="shop_now",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger"))
    bot.edit_message_text(f"📦 <b>{product[0]}</b>\n\nSelect duration:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

def process_purchase(call, product_id, plan_id):
    user_id = call.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    cursor.execute("SELECT price, days FROM plans WHERE id=?", (plan_id,))
    plan = cursor.fetchone()
    cursor.execute("SELECT name FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    price = plan[0]
    
    if not user or user[0] < price:
        bot.answer_callback_query(call.id, f"❌ Insufficient balance! Need ₹{price}", show_alert=True)
        cursor.close()
        conn.close()
        return
    cursor.execute("SELECT id, license_key FROM license_keys WHERE product_id=? AND plan_id=? AND used=0 LIMIT 1", (product_id, plan_id))
    key = cursor.fetchone()
    if not key:
        bot.answer_callback_query(call.id, "❌ Out of stock!", show_alert=True)
        cursor.close()
        conn.close()
        return
    new_bal = user[0] - price
    cursor.execute("UPDATE users SET balance=? WHERE id=?", (new_bal, user_id))
    cursor.execute("UPDATE license_keys SET used=1, used_by=?, used_at=CURRENT_TIMESTAMP WHERE id=?", (user_id, key[0]))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, details) VALUES (?,?,'purchase',?)",
                   (user_id, price, f"Bought {product[0]} - {plan[1]} days"))
    conn.commit()
    cursor.close()
    conn.close()
    caption = f"{ce("success")} <b>Purchase Successful!</b>\n\n{ce("shop")} {product[0]}\n{ce("fire")} <code>{key[1]}</code>\n{ce("money")} New Balance: ₹{new_bal}"
    try:
        bot.send_photo(call.message.chat.id, SUCCESS_IMG, caption=caption, parse_mode="HTML")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        bot.edit_message_text(caption, call.message.chat.id, call.message.message_id, parse_mode="HTML")
    bot.send_message(ADMIN_USER_ID, f"{ce("shop")} <b>New order!</b>\nUser: {user_id}\nProduct: {product[0]}\nAmount: ₹{price}", parse_mode="HTML")

def show_profile(call, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, balance, joined_at, banned, spin_count, last_spin_date FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        status = "🚫 Banned" if user[3] else "✅ Active"
        today = date.today().isoformat()
        spins_today = user[4] if user[5] == today else 0
        text = f"{ce("profile")} <b>Profile</b>\n\n{ce("success")} Premium ID: <code>{user_id}</code>\n{ce("profile")} @{user[0] or 'N/A'}\n{ce("money")} Balance: ₹{user[1]}\n{ce("fire")} Joined: {user[2][:10]}\n{ce("success")} {status}\n{ce("success")} Spins today: {spins_today}/1"
    else:
        text = f"{ce("success")}Profile not found."
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Back", callback_data="back_main",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger")))

def show_history(call, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lk.license_key, p.name, lk.used_at 
        FROM license_keys lk 
        JOIN products p ON lk.product_id=p.id 
        WHERE lk.used_by=? ORDER BY lk.used_at DESC LIMIT 20
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        text = f"{ce("danger")} No purchase history."
    else:
        text = f"{ce("success")} <b>Order History</b>\n\n"
        for r in rows:
            text += f"{ce("pencil")} {r[1]}\n{ce("success")} <code>{r[0]}</code>\n{ce("fire")} {r[2][:10]}\n\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Back", callback_data="back_main",icon_custom_emoji_id=EMOJIS["fail"][1], style="danger")))

def ask_amount(call):
    msg = bot.edit_message_text(f"{ce("money")} <b>Enter amount (₹):</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
    bot.register_next_step_handler(msg, receive_amount)

def receive_amount(message):
    user_id = message.from_user.id
    try:
        amount = int(message.text.strip())
        if amount < 10:
            bot.reply_to(message, f"{ce("danger")} Minimum ₹10")
            return
        qr_api = f"https://fampay.anujbots.xyz/qr.php?upi={UPI_ID}&amount={amount}"
        req = urllib.request.Request(qr_api, headers={'User-Agent': 'Mozilla/5.0'})
        raw = urllib.request.urlopen(req, timeout=20).read().decode()
        res = json.loads(raw)
        order_id = res.get("order_id") or res.get("data", {}).get("order_id")
        qr_url = res.get("qr_url") or res.get("data", {}).get("qr_url") or res.get("qr")
        if not order_id or not qr_url:
            bot.reply_to(message, f"{ce("danger")} QR failed. Try again.")
            return
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pending_payments (user_id, order_id, amount, status, created_at) VALUES (?,?,?,'pending',?)",
                       (user_id, order_id, amount, int(time.time())))
        conn.commit()
        cursor.close()
        conn.close()
        bot.send_photo(message.chat.id, qr_url, caption=f"💳 <b>Pay ₹{amount}</b>\n\nOrder ID: <code>{order_id}</code>\n⏳ Waiting...\nAuto-detection within 10 min.", parse_mode="HTML")
    except:
        bot.reply_to(message, "❌ Invalid amount.")

def handle_admin_actions(call, data):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    if data == "admin_add_product":
        bot.edit_message_text("📝 Send product name:", chat_id, msg_id)
        bot.register_next_step_handler(call.message, add_product)
    elif data == "admin_edit_product":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM products")
        prods = cursor.fetchall()
        cursor.close()
        conn.close()
        if not prods:
            bot.edit_message_text("No products.", chat_id, msg_id)
            return
        markup = InlineKeyboardMarkup()
        for p in prods:
            markup.add(InlineKeyboardButton(f"✏️ {p[1]}", callback_data=f"editprod_{p[0]}"))
        markup.add(InlineKeyboardButton("◀️ Cancel", callback_data="admin_panel"))
        bot.edit_message_text("Edit product:", chat_id, msg_id, reply_markup=markup)
    elif data == "admin_del_product":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM products")
        prods = cursor.fetchall()
        cursor.close()
        conn.close()
        if not prods:
            bot.edit_message_text("No products.", chat_id, msg_id)
            return
        markup = InlineKeyboardMarkup()
        for p in prods:
            markup.add(InlineKeyboardButton(f"🗑️ {p[1]}", callback_data=f"delprod_{p[0]}"))
        markup.add(InlineKeyboardButton("◀️ Cancel", callback_data="admin_panel"))
        bot.edit_message_text("Delete product:", chat_id, msg_id, reply_markup=markup)
    elif data == "admin_add_plan":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM products")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        if not products:
            bot.edit_message_text("❌ No products found.", chat_id, msg_id)
            return
        markup = InlineKeyboardMarkup()
        for p in products:
            markup.add(InlineKeyboardButton(f"📦 {p[1]}", callback_data=f"selectplanprod_{p[0]}")) 
        markup.add(InlineKeyboardButton("◀️ Back", callback_data="admin_panel")) 
        bot.edit_message_text("📦 Select Product For Plan", chat_id, msg_id, reply_markup=markup)
    elif data == "admin_del_plan":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
        "SELECT p.name, pl.id, pl.days, pl.price FROM plans pl JOIN products p ON pl.product_id=p.id")
        plans = cursor.fetchall()
        cursor.close()
        conn.close()
        if not plans:
            bot.edit_message_text("No plans.", chat_id, msg_id)
            return
        markup = InlineKeyboardMarkup()
        for pl in plans:
            markup.add(InlineKeyboardButton(f"🗑️ {pl[0]} - {pl[2]}d ₹{pl[3]}", callback_data=f"delplan_{pl[1]}"))
        markup.add(InlineKeyboardButton("◀️ Cancel", callback_data="admin_panel"))
        bot.edit_message_text("Delete plan:", chat_id, msg_id, reply_markup=markup)
    elif data == "admin_add_keys":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM products")
        prods = cursor.fetchall()
        cursor.close()
        conn.close()
        if not prods:
            bot.edit_message_text("No products.", chat_id, msg_id)
            return
        markup = InlineKeyboardMarkup()
        for p in prods:
            markup.add(InlineKeyboardButton(f"🔑 {p[1]}", callback_data=f"addkeys_prod_{p[0]}"))
        markup.add(InlineKeyboardButton("◀️ Cancel", callback_data="admin_panel"))
        bot.edit_message_text("Select product:", chat_id, msg_id, reply_markup=markup)
    elif data == "admin_list_keys":
        list_all_keys(call)
    elif data == "admin_del_key":
        bot.edit_message_text("🔑 Send key to delete:", chat_id, msg_id)
        bot.register_next_step_handler(call.message, delete_key)
    elif data == "admin_add_balance":
        bot.edit_message_text("💰 Send: <code>user_id amount</code>", chat_id, msg_id, parse_mode="HTML")
        bot.register_next_step_handler(call.message, add_balance_admin)
    elif data == "admin_remove_balance":
        bot.edit_message_text("💰 Send: <code>user_id amount</code>", chat_id, msg_id, parse_mode="HTML")
        bot.register_next_step_handler(call.message, remove_balance_admin)
    elif data == "admin_ban_user":
        bot.edit_message_text("🚫 Send user ID to ban:", chat_id, msg_id)
        bot.register_next_step_handler(call.message, ban_user_cmd)
    elif data == "admin_unban_user":
        bot.edit_message_text("✅ Send user ID to unban:", chat_id, msg_id)
        bot.register_next_step_handler(call.message, unban_user_cmd)
    elif data == "admin_stats":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM license_keys")
        keys = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='purchase'")
        sales = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM users WHERE banned=1")
        banned = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        bot.edit_message_text(f"📊 <b>Stats</b>\n\n👥 Users: {users}\n🔑 Keys: {keys}\n💰 Sales: ₹{sales}\n🚫 Banned: {banned}", chat_id, msg_id, parse_mode="HTML")

def add_product(message):
    name = message.text.strip()
    if name:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name) VALUES (?)", (name,))
        conn.commit()
        cursor.close()
        conn.close()
        bot.reply_to(message, f"✅ Product '{name}' added.")
    else:
        bot.reply_to(message, "❌ Invalid name.")

def edit_product_name(message, prod_id):
    name = message.text.strip()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name=? WHERE id=?", (name, prod_id))
    conn.commit()
    cursor.close()
    conn.close()
    bot.reply_to(message, f"✅ Product updated to '{name}'.")

def add_plan(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    if not state:
        bot.reply_to(message, "❌ Session Expired")
        return
    product_id = state.get("plan_product_id")
    try:
        days, price = message.text.split()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO plans (product_id, days, price) VALUES (?, ?, ?)",
            (product_id, days, price)
        )
        conn.commit()
        cursor.close()
        conn.close()
        user_states.pop(user_id, None)
        bot.reply_to(message, "✅ Plan Added Successfully")
    except:
        bot.reply_to(message, "❌ Format:\n30 499")

def add_balance_admin(message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        bot.reply_to(message, "Format: user_id amount")
        return
    uid, amt = parts
    amt = int(amt)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amt, uid))
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO users (id, balance) VALUES (?,?)", (uid, amt))
    conn.commit()
    cursor.close()
    conn.close()
    bot.reply_to(message, f"✅ Added ₹{amt} to {uid}")
    try:
        bot.send_message(int(uid), f"🎉 Admin added ₹{amt} to your balance!")
    except:
        pass

def remove_balance_admin(message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        bot.reply_to(message, "Format: user_id amount")
        return
    uid, amt = parts
    amt = int(amt)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ? AND balance >= ?", (amt, uid, amt))
    if cursor.rowcount == 0:
        bot.reply_to(message, "❌ User not found or insufficient balance.")
    else:
        conn.commit()
        bot.reply_to(message, f"✅ Removed ₹{amt} from {uid}")
        try:
            bot.send_message(int(uid), f"⚠️ Admin removed ₹{amt} from your balance.")
        except:
            pass
    cursor.close()
    conn.close()

def ban_user_cmd(message):
    try:
        uid = int(message.text.strip())
        ban_user(uid)
        bot.reply_to(message, f"✅ User {uid} banned.")
        try:
            bot.send_message(uid, "⛔ You have been banned. Contact support.")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Invalid ID.")

def unban_user_cmd(message):
    try:
        uid = int(message.text.strip())
        unban_user(uid)
        bot.reply_to(message, f"✅ User {uid} unbanned.")
        try:
            bot.send_message(uid, "✅ You have been unbanned. Use /start again.")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Invalid ID.")

def receive_keys(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    if state.get("action") != "add_keys_final":
        bot.reply_to(message, "Session expired. Start over.")
        return
    prod_id = state.get("prod_id")
    plan_id = state.get("plan_id")
    if not prod_id or not plan_id:
        bot.reply_to(message, "Error: missing data.")
        return
    keys = [k.strip() for k in message.text.split('\n') if k.strip()]
    if not keys:
        bot.reply_to(message, "No keys provided.")
        return
    conn = get_db()
    cursor = conn.cursor()
    inserted = 0
    for k in keys:
        try:
            cursor.execute("INSERT INTO license_keys (product_id, plan_id, license_key) VALUES (?,?,?)", (prod_id, plan_id, k))
            inserted += 1
        except sqlite3.IntegrityError:
            bot.send_message(message.chat.id, f"Duplicate: {k}")
    conn.commit()
    cursor.close()
    conn.close()
    bot.reply_to(message, f"✅ {inserted} keys added.")
    user_states.pop(user_id, None)

def delete_key(message):
    key_str = message.text.strip()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM license_keys WHERE license_key = ?", (key_str,))
    if cursor.rowcount:
        conn.commit()
        bot.reply_to(message, "✅ Key deleted.")
    else:
        bot.reply_to(message, "❌ Key not found.")
    cursor.close()
    conn.close()

def list_all_keys(call):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lk.license_key, p.name, pl.days, lk.used, lk.used_by
        FROM license_keys lk
        JOIN products p ON lk.product_id=p.id
        JOIN plans pl ON lk.plan_id=pl.id
        ORDER BY lk.id DESC LIMIT 30
    """)
    keys = cursor.fetchall()
    cursor.close()
    conn.close()
    if not keys:
        bot.edit_message_text("No keys found.", call.message.chat.id, call.message.message_id)
        return
    text = "🔑 <b>Keys</b>\n\n"
    for k in keys:
        status = f"{ce('success')} Active" if not k[3] else "❌ Used"
        text += f"📦 {k[1]} ({k[2]}d)\n🔑 <code>{k[0]}</code>\nStatus: {status}\n"
        if k[3]:
            text += f"👤 Used by: {k[4]}\n"
        text += "\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

if __name__ == "__main__":
    init_db()

    payment_thread = threading.Thread(
        target=check_payments,
        daemon=True
    )
    payment_thread.start()

    print("🚀 Bot Started Successfully")

    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                skip_pending=True
            )
        except Exception as e:
            print(f"Polling Error: {e}")
            try:
                bot.stop_polling()
            except:
                pass
            time.sleep(5)