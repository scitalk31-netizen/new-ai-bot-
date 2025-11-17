# bot.py
import os
import logging
import google.generativeai as genai
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# =======================
# CONFIG (Your values added)
# =======================
TELEGRAM_TOKEN = "8253275091:AAFFfNmtmBQEMIAExQr918r8ew91u77TS-A"
GEMINI_API_KEY = "AIzaSyBCQrFQMGEZErvLv5F7fnc8bPPC9jMWXxc"
ALLOWED_GROUP_ID = -1002628845430
GROUP_LINK = "https://t.me/pesurubooks01"
BOT_NAME = "SciU"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =======================
# GEMINI INIT
# =======================
genai.configure(api_key=GEMINI_API_KEY)
text_model = genai.GenerativeModel("gemini-pro")
vision_model = genai.GenerativeModel("gemini-pro-vision")

# Memory for verified joined users
verified_users = set()

# =======================
# MAIN MENU UI
# =======================
def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("❓ සාමාන්‍ය ප්‍රශ්න", callback_data="ask_short"),
            InlineKeyboardButton("🔢 පියවරෙන් පියවර", callback_data="ask_step")
        ],
        [InlineKeyboardButton("📷 Image Analyze", callback_data="photo")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# =======================
# GROUP JOIN CHECK
# =======================
async def check_group_membership(context, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(ALLOWED_GROUP_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

async def require_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user

    if not user:
        return False

    # If previously verified -> allow
    if user.id in verified_users:
        return True

    # If user already in group -> verify now
    already_in = await check_group_membership(context, user.id)
    if already_in:
        verified_users.add(user.id)
        return True

    # Ask user to join + forward a message
    await update.message.reply_text(
        f"❌ ඔබ *{BOT_NAME}* DM භාවිතා කිරීමට පෙර group එක join විය යුතුයි.\n\n"
        f"👉 Group link: {GROUP_LINK}\n\n"
        "Join උනාම: \n"
        "➡️ *Group එකෙන් 'Hi' කියලා msg එකක් 보내න්න*\n"
        "➡️ එම msg එක DM එකට forward කරන්න\n\n"
        "Forward කළ ගමන් access ලබාදිමි ❤️",
        parse_mode="Markdown"
    )
    return False

# =======================
# FORWARDED MESSAGE VERIFY
# =======================
async def forward_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.forward_from_chat:
        return

    # Check if forwarded from correct group
    if update.message.forward_from_chat.id == ALLOWED_GROUP_ID:
        user = update.effective_user
        verified_users.add(user.id)

        await update.message.reply_text(
            "✅ ඔබ group එක join වී ඇති බව සනාථ කරන ලදී!\n"
            "දැන් Bot එක ඔබට සම්පූර්ණයෙන්ම ලබාගත හැක.\n\n"
            "👉 `/start` යලි type කරන්න ❤️"
        )

# =======================
# /start
# =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 හෙලෝ! මම *{BOT_NAME}* — ඔබේ A/L Science AI Tutor.\n\n"
        "ඔබට මෙහෙම යොදාගන්න පුළුවන්:\n"
        "• `/q <ප්‍රශ්නය>` — සාමාන්‍ය පිළිතුර\n"
        "• `/qstep <ප්‍රශ්නය>` — පියවරෙන් පියවර A/L style\n"
        "• Photo — AI Image Analyze (Diagrams / Experiments)\n\n"
        "👇 පහතින් service එකක් තෝරන්න",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# =======================
# BUTTON HANDLER
# =======================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cmd = q.data

    if cmd == "ask_short":
        await q.edit_message_text("❓ `/q <your question>` ලෙස අහන්න.")
    elif cmd == "ask_step":
        await q.edit_message_text("🔢 `/qstep <your question>` ලෙස අහන්න.")
    elif cmd == "photo":
        await q.edit_message_text("📷 Analyze කිරීමට image එකක් යොමුකරන්න.")
    elif cmd == "help":
        await q.edit_message_text(
            f"🟦 HELP MENU\n"
            "• /q — Normal Answer\n"
            "• /qstep — Step-by-step A/L mode\n"
            "• Send a photo — Analyze\n\n"
            f"⚠️ Group join link: {GROUP_LINK}"
        )

# =======================
# A/L Friendly Prompt Builder
# =======================
def build_AL_prompt(question):
    return (
        "You are an expert Sri Lankan A/L science teacher. "
        "Explain everything clearly in simple Sinhala. "
        "Always include:\n"
        "1. Basic idea\n"
        "2. Theory\n"
        "3. A/L syllabus relevance\n"
        "4. Examples\n"
        "5. Short summary\n\n"
        f"Question: {question}"
    )

# =======================
# /q (Normal Answer)
# =======================
async def q_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_join(update, context):
        return

    question = " ".join(context.args)
    if not question:
        return await update.message.reply_text("❗ `/q <question>` ලෙස අහන්න.")

    await update.message.reply_text("⏳ සකස් වෙමින්...")

    try:
        resp = text_model.generate_content(build_AL_prompt(question))
        await update.message.reply_text(resp.text)
    except:
        await update.message.reply_text("⚠️ AI error!")

# =======================
# /qstep (Step-by-step)
# =======================
async def qstep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_join(update, context):
        return

    question = " ".join(context.args)
    if not question:
        return await update.message.reply_text("❗ `/qstep <question>` ලෙස අහන්න.")

    await update.message.reply_text("⏳ Step-by-step answer සකස් වෙමින්...")

    try:
        prompt = (
            "Sri Lankan A/L teacher mode: give answer in **clear numbered steps**.\n\n"
            + build_AL_prompt(question)
        )
        resp = text_model.generate_content(prompt)
        await update.message.reply_text(resp.text)
    except:
        await update.message.reply_text("⚠️ AI error!")

# =======================
# IMAGE ANALYZE
# =======================
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_join(update, context):
        return

    await update.message.reply_text("📷 Image analyze වෙමින්...")

    photo = update.message.photo[-1]
    file = await photo.get_file()
    img_path = f"img_{update.message.message_id}.jpg"
    await file.download_to_drive(img_path)

    try:
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

        prompt = (
            "You are an A/L science teacher.\n"
            "Analyze this image in simple Sinhala.\n"
            "Explain:\n"
            "1. What it shows\n"
            "2. The scientific theory\n"
            "3. A/L syllabus relevance\n"
            "4. Key points\n"
        )

        resp = vision_model.generate_content([
            prompt,
            genai.types.Part.from_file(img_path, mime_type="image/jpeg")
        ])

        await update.message.reply_text(resp.text)
    except:
        await update.message.reply_text("⚠️ Image Analyze error!")
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)

# =======================
# PRIVATE CHAT MESSAGES
# =======================
async def private_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_join(update, context):
        return

    txt = update.message.text

    await update.message.reply_text("⏳ සකස් වෙමින්...")
    try:
        resp = text_model.generate_content(build_AL_prompt(txt))
        await update.message.reply_text(resp.text)
    except:
        await update.message.reply_text("⚠️ Error!")

# =======================
# MAIN
# =======================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.FORWARDED, forward_verify))
    app.add_handler(CommandHandler("q", q_handler))
    app.add_handler(CommandHandler("qstep", qstep_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, private_text))

    print(f"{BOT_NAME} Running…")
    app.run_polling()

if __name__ == "__main__":
    main()
