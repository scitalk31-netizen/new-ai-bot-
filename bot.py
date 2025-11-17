# bot.py
import os
import asyncio
import logging
import google.generativeai as genai
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.constants import ChatAction  # ✅ fixed import
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ---------- CONFIG ----------
TELEGRAM_TOKEN = "8253275091:AAFFfNmtmBQEMIAExQr918r8ew91u77TS-A"  # replace with your bot token
GEMINI_API_KEY = "AIzaSyBCQrFQMGEZErvLv5F7fnc8bPPC9jMWXxc"          # replace with your Gemini API key
ALLOWED_GROUP_ID = -1002628845430                                    # replace with your group id
GROUP_LINK = "https://t.me/pesurubooks01"                             # official group link
BOT_NAME = "SciU"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Gemini init ----------
genai.configure(api_key=GEMINI_API_KEY)
text_model = genai.GenerativeModel("gemini-pro")
vision_model = genai.GenerativeModel("gemini-pro-vision")

# ---------- Helpers ----------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("❓ ප්‍රශ්නය (short)", callback_data="ask_short"),
         InlineKeyboardButton("🔢 Answer with step", callback_data="ask_step")],
        [InlineKeyboardButton("📷 රූපය විශ්ලේෂණය", callback_data="photo")],
        [InlineKeyboardButton("ℹ️ උපකාරය", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def is_user_in_allowed_group(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=ALLOWED_GROUP_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.warning("Membership check failed: %s", e)
        return False

async def require_group_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat and update.effective_chat.id == ALLOWED_GROUP_ID:
        return True

    user = update.effective_user
    if not user:
        return False

    in_group = await is_user_in_allowed_group(context, user.id)
    if not in_group:
        join_msg = (
            f"❗ SciU හැසිරවීමට පෙර ඔබ අපගේ official group එකට සාමාජික විය යුතුයි.\n\n"
            f"👉 Group link: {GROUP_LINK}\n\n"
            "Group එකට එකතු වුණ පසු නැවත මේක run කරන්න."
        )
        await update.message.reply_text(join_msg)
        return False
    return True

# ---------- Command Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"👋 හෙලෝ! මම *{BOT_NAME}* — ඔබේ Sci/Tech උදව්කරුවා.\n\n"
        "පහත බටන් වලින් ඔබට පහසු සේවා ලබාගත හැක.\n"
        "• /q <ප්‍රශ්නය> — සාමාන්‍ය උත්තර\n"
        "• /qstep <ප්‍රශ්නය> — පියවරෙන් පියවර උත්තර\n\n"
        "Buttons හරහා අත්හදා බලන්න."
    )
    await update.message.reply_text(text, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "ask_short":
        await query.edit_message_text("❓ ප්‍රශ්නය `/q ඔබේ ප්‍රශ්නය` ලෙස ටයිප් කරන්න. (සිංහල හෝ English)")
    elif data == "ask_step":
        await query.edit_message_text("🔢 පියවරෙන් පියවර උත්තර ලබාගැනීමට `/qstep ඔබේ ප්‍රශ්නය` ලෙස අහන්න.")
    elif data == "photo":
        await query.edit_message_text("📷 රූපයක් පහලට ඇතුලත් කරන්න. මම Sinhalaෙන් විස්තරකරමි.")
    elif data == "help":
        await query.edit_message_text(
            f"🟦 HELP\n"
            "/q <ප්‍රශ්නය> — සාමාන්‍ය උත්තර\n"
            "/qstep <ප්‍රශ්නය> — පියවරෙන් පියවර උත්තර\n"
            "Send a photo — analyze image\n\n"
            f"Note: Direct use (DM) requires you to be a member of the official group: {GROUP_LINK}"
        )

# ---------- Q Handlers ----------
async def q_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_group_membership(update, context):
        return

    question = " ".join(context.args).strip()
    if not question:
        await update.message.reply_text("❗ `/q ඔබේ ප්‍රශ්නය` ලෙස අහන්න.")
        return

    await update.message.reply_text("⏳ පිළිතුර සකස් වෙමින්...")
    try:
        prompt = f"ඔබේ කාර්යය: පහත ප්‍රශ්නයට සාමාන්‍ය, සරල සිංහලෙන් උත්තර දෙන්න.\n\nප්‍රශ්නය: {question}"
        resp = text_model.generate_content(prompt)
        await update.message.reply_text(resp.text)
    except Exception as e:
        logger.exception("Gemini error:")
        await update.message.reply_text("⚠️ Gemini API error. පසුව උත්සහ කරන්න.")

async def qstep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_group_membership(update, context):
        return

    question = " ".join(context.args).strip()
    if not question:
        await update.message.reply_text("❗ `/qstep ඔබේ ප්‍රශ්නය` ලෙස අහන්න.")
        return

    await update.message.reply_text("⏳ පියවරෙන් පියවර පිළිතුර සකස් වෙමින්...")
    try:
        prompt = (
            "ඔබේ කාර්යය: පහත ප්‍රශ්නයට සිංහලෙන් **පියවරෙන් පියවර (numbered steps)** අකාරයෙන් උත්තර දෙන්න. "
            "වැඩි විස්තර සහ practical steps එකතු කරන්න.\n\n"
            f"ප්‍රශ්නය: {question}"
        )
        resp = text_model.generate_content(prompt)
        await update.message.reply_text(resp.text)
    except Exception as e:
        logger.exception("Gemini error:")
        await update.message.reply_text("⚠️ Gemini API error. පසුව උත්සහ කරන්න.")

# ---------- Photo handler ----------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_group_membership(update, context):
        return

    await update.message.reply_text("📷 රූපය විශ්ලේෂණය වෙමින්…")
    photo = update.message.photo[-1]
    file = await photo.get_file()
    img_path = f"img_{update.message.message_id}.jpg"
    await file.download_to_drive(img_path)

    try:
        # Telegram typing action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        response = vision_model.generate_content([
            "Explain this image in detailed, friendly Sinhala and list any important observations.",
            genai.types.Part.from_file(img_path, mime_type="image/jpeg")
        ])
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.exception("Vision error:")
        await update.message.reply_text("⚠️ රූපය විශ්ලේෂණය කිරීමට නොහැකි විය.")
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)

# ---------- Text handler ----------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    text = update.message.text or ""
    if chat.type != "private" and not text.startswith("/q") and f"@{context.bot.username}" not in text:
        return

    if not await require_group_membership(update, context):
        return

    await update.message.reply_text("⏳ පිළිතුර සකස් වෙමින්...")
    try:
        prompt = f"User message: {text}\nReply in friendly Sinhala."
        resp = text_model.generate_content(prompt)
        await update.message.reply_text(resp.text)
    except Exception:
        await update.message.reply_text("⚠️ පිළිතුර ලබාගැනීමට ගැටලුවක් තිබේ.")

# ---------- Main ----------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("q", q_handler))
    app.add_handler(CommandHandler("qstep", qstep_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print(f"{BOT_NAME} bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
