import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ====================== CONFIG ======================
BOT_TOKEN = "8610622953:AAHWGyMq60inMKwI7s25bL0A3dZmyX6m8N0"   # अपना टोकन
DB_PATH = "Abhinav_Dad.db"                               # डेटाबेस फाइल

# ====================== DATABASE ======================
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ====================== BOT ======================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # यूज़र को टेबल में डालें (अगर नहीं है तो)
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, message.from_user.username or "N/A"))
    conn.commit()
    c.close()
    conn.close()

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📋 View My Data", callback_data="view_data"),
        InlineKeyboardButton("🗑️ Delete All My Data", callback_data="delete_all")
    )
    bot.send_message(
        message.chat.id,
        "👋 Welcome! Choose an option below:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if call.data == "view_data":
        # डेटा फेच करें
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT username, balance, verified, phone_number, spin_count, last_spin_date, banned FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user:
            bot.edit_message_text("❌ आपका डेटा नहीं मिला। कृपया /start करें।", chat_id, msg_id)
            c.close()
            conn.close()
            return
        
        # ट्रांजैक्शन हिस्ट्री (पिछली 5)
        c.execute("SELECT amount, type, details, created_at FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (user_id,))
        transactions = c.fetchall()
        c.close()
        conn.close()

        # डेटा को फॉर्मेट करें
        username = user['username'] or "N/A"
        balance = user['balance']
        verified = "✅ हाँ" if user['verified'] else "❌ नहीं"
        phone = user['phone_number'] or "नहीं दिया"
        spin_count = user['spin_count']
        last_spin = user['last_spin_date'] or "कभी नहीं"
        banned = "🚫 हाँ" if user['banned'] else "✅ नहीं"

        text = f"<b>📋 आपका डेटा</b>\n\n"
        text += f"🆔 ID: <code>{user_id}</code>\n"
        text += f"👤 यूज़रनेम: @{username}\n"
        text += f"💰 बैलेंस: ₹{balance}\n"
        text += f"📱 फोन नंबर: {phone}\n"
        text += f"✅ वेरिफाइड: {verified}\n"
        text += f"🎰 स्पिन आज: {spin_count}/1 (आखिरी: {last_spin})\n"
        text += f"🚫 बैन: {banned}\n\n"

        if transactions:
            text += "<b>📜 पिछली 5 ट्रांजैक्शन:</b>\n"
            for t in transactions:
                amount = t['amount']
                typ = t['type']
                details = t['details'] or ""
                date_str = t['created_at'][:16] if t['created_at'] else ""
                sign = "+" if typ in ['add_money', 'spin'] else "-"
                text += f"• {sign}₹{amount} ({typ}) {details} - {date_str}\n"
        else:
            text += "📭 कोई ट्रांजैक्शन नहीं।"

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🔙 Back", callback_data="back_main"),
            InlineKeyboardButton("🗑️ Delete All Data", callback_data="delete_all")
        )
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML", reply_markup=markup)

    elif call.data == "delete_all":
        # पुष्टि लें
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ हाँ, पूरा डिलीट करो", callback_data="confirm_delete"),
            InlineKeyboardButton("❌ नहीं, रद्द करो", callback_data="back_main")
        )
        bot.edit_message_text(
            "⚠️ <b>क्या आप सच में अपना सारा डेटा डिलीट करना चाहते हैं?</b>\n"
            "इसमें आपका फोन नंबर, बैलेंस, स्पिन डेटा, और सभी ट्रांजैक्शन हट जाएँगे।\n"
            "यह <b>वापस नहीं</b> आ सकता!",
            chat_id, msg_id, parse_mode="HTML", reply_markup=markup
        )

    elif call.data == "confirm_delete":
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        c.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM pending_payments WHERE user_id = ?", (user_id,))
        conn.commit()
        c.close()
        conn.close()

        bot.edit_message_text(
            "✅ <b>आपका सारा डेटा सफलतापूर्वक डिलीट कर दिया गया है!</b>\n"
            "अब /start करके नए सिरे से शुरू कर सकते हैं।",
            chat_id, msg_id, parse_mode="HTML"
        )

    elif call.data == "back_main":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📋 View My Data", callback_data="view_data"),
            InlineKeyboardButton("🗑️ Delete All My Data", callback_data="delete_all")
        )
        bot.edit_message_text(
            "👋 मुख्य मेनू – आप क्या करना चाहेंगे?",
            chat_id, msg_id, reply_markup=markup
        )

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.reply_to(message, "कृपया /start दबाएँ।")

# ====================== RUN ======================
if __name__ == "__main__":
    print("🚀 View & Delete Bot चल रहा है...")
    bot.infinity_polling()
