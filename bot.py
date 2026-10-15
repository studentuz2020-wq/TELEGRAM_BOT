import asyncio
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv
from translator import translate_text
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

LANGUAGES = {
    "uz": "🇺🇿 O'zbekcha",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "tr": "🇹🇷 Türkçe",
    "de": "🇩🇪 Deutsch",
    "fr": "🇫🇷 Français",
    "es": "🇪🇸 Español",
    "ar": "🇸🇦 العربية",
    "zh-CN": "🇨🇳 中文",
    "ko": "🇰🇷 한국어",
}
DEFAULT_LANG = "uz"


def lang_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(name, callback_data=f"lang:{code}")
        for code, name in LANGUAGES.items()
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Salom! Men tarjima botman 🌍\n\n"
        "Menga istalgan matnni yuboring — men uni tanlangan tilga tarjima qilaman.\n"
        "Tilni tanlash: /lang\n"
        "Yordam: /help"
    )
    await lang_command(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Buyruqlar:\n"
        "/start - botni ishga tushirish\n"
        "/lang - tarjima tilini tanlash\n"
        "/help - yordam\n\n"
        "Shunchaki matn yuboring, bot tarjima qiladi."
    )


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current = context.user_data.get("lang", DEFAULT_LANG)
    await update.message.reply_text(
        f"Qaysi tilga tarjima qilay? (hozir: {LANGUAGES[current]})",
        reply_markup=lang_keyboard(),
    )


async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 1)[1]
    if code in LANGUAGES:
        context.user_data["lang"] = code
        await query.edit_message_text(
            f"✅ Tarjima tili: {LANGUAGES[code]}\nEndi matn yuboring."
        )


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    target = context.user_data.get("lang", DEFAULT_LANG)
    try:
        result = await translate_text(text, target)
        await update.message.reply_text(f"{LANGUAGES[target]}:\n\n{result}")
    except Exception:
        logging.exception("Translation error")
        await update.message.reply_text(
            "❌ Tarjima qilishda xatolik. Keyinroq urinib ko'ring."
        )


def start_health_server() -> None:
    """Hosting PORT bersa, oddiy HTTP server ishga tushiradi (Render uchun)."""
    port = os.getenv("PORT")
    if not port:
        return

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("0.0.0.0", int(port)), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logging.info("Health server %s-portda ishlamoqda", port)


def main() -> None:
    if not TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. .env faylini tekshiring.")
    start_health_server()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("lang", lang_command))
    app.add_handler(CallbackQueryHandler(lang_callback, pattern=r"^lang:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))
    logging.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
