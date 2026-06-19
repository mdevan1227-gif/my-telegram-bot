import asyncio
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "8774795995"  # ⚠️ Put your token here
ADMIN_ID = 5133262086          # ⚠️ Put your numeric ID here
BOT_USERNAME = "Galaryi_bot"  # ⚠️ Put your bot username here

video_database = {}

# --- DUMMY WEB SERVER FOR RENDER ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- BOT HANDLERS ---
async def handle_admin_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    video_file_id = update.message.video.file_id
    unique_key = f"vid_{len(video_database) + 1001}"
    video_database[unique_key] = video_file_id
    share_link = f"https://t.me/{BOT_USERNAME}?start={unique_key}"
    await update.message.reply_text(f"✅ **Saved!**\n\nLink:\n`{share_link}`", parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat_id = update.effective_chat.id
    if not args:
        await update.message.reply_text("Welcome! Send me a valid link.")
        return
    unique_key = args[0]
    if unique_key in video_database:
        video_id = video_database[unique_key]
        sent_message = await context.bot.send_video(chat_id=chat_id, video=video_id, caption="⚠️ Clears in 10 minutes!")
        asyncio.create_task(delete_message_after_delay(context, chat_id, sent_message.message_id, delay=600))
    else:
        await update.message.reply_text("❌ Link expired or invalid.")

async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        await context.bot.send_message(chat_id=chat_id, text="⏱️ Time's up! Video cleared.")
    except Exception as e:
        print(f"Delete failed: {e}")

def main():
    # Start the dummy website in the background so Render stays happy
    threading.Thread(target=run_health_check, daemon=True).start()

    # Start the Telegram Bot
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO & filters.Chat(ADMIN_ID), handle_admin_video))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
