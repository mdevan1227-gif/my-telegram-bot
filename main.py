import asyncio
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import firebase_admin
from firebase_admin import credentials, db
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "8774795995:AAE6LpC5x5_J7MeLQgFh6uduu2g1YSFOPxI"
ADMIN_ID = 5133262086
BOT_USERNAME = "Galaryi_bot"

# --- INITIALIZE FIREBASE ---
firebase_json = os.environ.get("FIREBASE_JSON")
if firebase_json:
    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)
    # ⚠️ REPLACE THE LINK BELOW WITH YOUR REAL FIREBASE DATABASE LINK
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://console.firebase.google.com/u/1/project/prihec-f6d98/database/prihec-f6d98-default-rtdb/data/~2F'
    })
else:
    print("❌ Firebase JSON environment variable is missing!")

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
    
    # Save permanently to Firebase Realtime Database
    ref = db.reference('videos')
    new_video_ref = ref.push()
    unique_key = new_video_ref.key
    new_video_ref.set(video_file_id)
    
    share_link = f"https://t.me/{BOT_USERNAME}?start={unique_key}"
    await update.message.reply_text(f"✅ **Saved Permanently to Database!**\n\nLink:\n`{share_link}`", parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat_id = update.effective_chat.id
    
    if not args:
        await update.message.reply_text("Welcome! Send me a valid link to view a video.")
        return
    
    unique_key = args[0]
    
    # Check Firebase database for the video file ID
    video_ref = db.reference(f'videos/{unique_key}').get()
    
    if video_ref:
        # Send the video to the user
        sent_message = await context.bot.send_video(
            chat_id=chat_id, 
            video=video_ref, 
            caption="⚠️ This video will automatically clear from this chat in 10 minutes!"
        )
        
        # Start a 10-minute (600 seconds) countdown to delete ONLY the message from their chat screen
        asyncio.create_task(delete_message_after_delay(context, chat_id, sent_message.message_id, delay=600))
    else:
        await update.message.reply_text("❌ Link expired or invalid.")

async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Delete failed: {e}")

def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO & filters.Chat(ADMIN_ID), handle_admin_video))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
