# bot.py
import os
import asyncio
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

# ---------- CONFIG ----------
TELEGRAM_TOKEN = "8253275091:AAFFfNmtmBQEMIAExQr918r8ew91u77TS-A"
GEMINI_API_KEY = "AIzaSyBCQrFQMGEZErvLv5F7fnc8bPPC9jMWXxc"
ALLOWED_GROUP_ID = -1002628845430
GROUP_LINK = "https://t.me/pesurubooks01"
BOT_NAME = "SciU"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Gemini init ----------
genai.configure(api_key=GEMINI_API_KEY)
text_model = genai.GenerativeModel("gemini-pro")
vision_model = genai.GenerativeModel("gemini-pro-vision")

# ---------- UI: Main Menu Buttons ----------
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

# ---------- GROUP CHECK ----------
async def is_user_in_allowed_group(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(ALLOWED_GROUP_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

async def require_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False

    joined = await is_user_in_allowed_group(context, user.id)

    if not joined:
        msg = (
            "❌ *ඔබ SciU Official Group එකට join වී නෑ!*\n\n"
            "Bot එක භාවිතා කරන්න එතනට join වෙන්න.\n\n"
            f"👉 Group link: {GROUP_LINK}\n\n"
            "Join වූ පසු `/start` යලි type කරන්න."
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return False
    return True

# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"👋 හෙලෝ! මම *{BOT_NAME}* — ඔබේ විද්‍යා / තාක්ෂණ AI උපකාරකයා.\n\n"
        "ඔබට මෙහෙම යොදාගන්න පුළුවන්:\n"
        "• `/q <ප්‍රශ්නය>` — සාමාන්‍ය පිළිතුර\n"
        "• `/qstep <ප්‍රශ්නය>` — පියවරෙන් පියවර පිළිතුර\n"
        "• Photo යවන්න — AI Image Analyze\n\n"
        "👇 පහත menu එකෙන් service එකක් තෝරන්න"
    )
    await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")

# ---------- BUTTON HANDLER ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd = query.data

    if cmd == "ask_short":
        await query.edit_message_text("❓ `/q ඔබේ ප්‍රශ්නය` ලෙස අහන්න.")
    elif cmd == "ask_step":
        await query.edit_message_text("🔢 `/qstep ඔබේ ප්‍රශ්නය` ලෙස අහන්න (numbered steps).")
    elif cmd == "photo":
        await query.edit_message_text("📷 Analyze කරන්න image එකක් යොමු කරන්න.")
    elif cmd == "help":
        await query.edit_message_text(
            f"🟦 HELP GUIDE\n"
            "• /q <text> — සාමාන්‍ය answer\n"
            "• /qstep <text> — Step-by-step answer\n"
            "• Send a photo — image analysis\n\n"
            f"⚠️ Direct use සඳහා group join වීම අවශ්‍යයි: {GROUP_LINK}"
        )

# ---------- /q ----------
async def q_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_group(update, context):
        return

    question = " ".join(context.args)
    if not question:
        await update.message.reply_text("❗ `/q <text>` ලෙස අහන්න.")
        return

    await update.message.reply_text("⏳ සකස් වෙමින්...")

    try:
        prompt = (
            "පහත ප්‍රශ්නයට සරල, පැහැදිලි සිංහලෙන් පිළිතුර ලබාදෙන්න.\n\n"
            f"ප්‍රශ්නය: {question}"
        )
        resp = text_model.generate_content(prompt)
        await update.message.reply_text(resp.text)
    except:
        await update.message.reply_text("⚠️ Gemini API error!")

# ---------- /qstep ----------
async def qstep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_group(update, context):
        return

    question = " ".join(context.args)
    if not question:
        await update.message.reply_text("❗ `/qstep <text>` ලෙස අහන්න.")
        return

    await update.message.reply_text("⏳ Step-by-step සකස් වෙමින්...")

    try:
        prompt = (
            "පහත ප්‍රශ්නයට **පියවරෙන් පියවර (numbered)** සිංහලෙන් පිළිතුර දෙන්න.\n\n"
            f"ප්‍රශ්නය: {question}"
        )
        resp = text_model.generate_content(prompt)
        await update.message.reply_text(resp.text)
    except:
        await update.message.reply_text("⚠️ Gemini API error!")

# ---------- IMAGE ANALYZE ----------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_group(update, context):
        return

    await update.message.reply_text("📷 රූපය විශ්ලේෂණය වෙමින්…")

    photo = update.message.photo[-1]
    file = await photo.get_file()

    img = f"img_{update.message.message_id}.jpg"
    await file.download_to_drive(img)

    try:
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

        response = vision_model.generate_content([
            "Explain this image in friendly, clear Sinhala.",
            genai.types.Part.from_file(img, mime_type="image/jpeg")
        ])

        await update.message.reply_text(response.text)
    except:
        await update.message.reply_text("⚠️ Image Analyze error!")
    finally:
        if os.path.exists(img):
            os.remove(img)

# ---------- PRIVATE TEXT HANDLER ----------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    # Ignore normal chat unless DM or @mention
    if update.effective_chat.type != "private" and f"@{context.bot.username}" not in text:
        return

    if not await require_group(update, context):
        return

    await update.message.reply_text("⏳ සකස් වෙමින්...")

    try:
        prompt = f"User message: {text}\nReply in natural Sinhala."
        resp = text_model.generate_content(prompt)
        await update.message.reply_text(resp.text)
    except:
        await update.message.reply_text("⚠️ Error!")

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("q", q_handler))
    app.add_handler(CommandHandler("qstep", qstep_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print(f"{BOT_NAME} is running…")
    app.run_polling()

if __name__ == "__main__":
    main()
