import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "8774795995"
ADMIN_ID = 5133262086  # Replace with your actual numerical Telegram ID
BOT_USERNAME = "@Galaryi_bot" # e.g., photo_video_share_bot

# In-memory database (For production, use SQLite, MongoDB, or Firebase)
video_database = {}

# --- ADMIN HANDLER: Generate Link ---
async def handle_admin_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check if the user is the admin
    if user_id != ADMIN_ID:
        return

    # Get the video file ID
    video_file_id = update.message.video.file_id
    
    # Create a unique tracking ID based on current database size
    unique_key = f"vid_{len(video_database) + 1001}"
    
    # Save to our database mapping
    video_database[unique_key] = video_file_id
    
    # Generate the deep link
    share_link = f"https://t.me/{BOT_USERNAME}?start={unique_key}"
    
    await update.message.reply_text(
        f"✅ **Video Saved Successfully!**\n\n"
        f"Here is your sharing link:\n`{share_link}`",
        parse_mode="Markdown"
    )

# --- USER HANDLER: Process Link Click (/start) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args  # Captures anything after /start (e.g., vid_1001)
    chat_id = update.effective_chat.id

    if not args:
        await update.message.reply_text("Welcome! Send me a valid video access link to view content.")
        return

    unique_key = args[0]

    # Look up the key in our database
    if unique_key in video_database:
        video_id = video_database[unique_key]
        
        # Send the video to the user
        sent_message = await context.bot.send_video(
            chat_id=chat_id, 
            video=video_id, 
            caption="⚠️ This video will self-destruct in 10 minutes. Watch it now!"
        )
        
        # Start a background task to delete the video after 10 minutes
        asyncio.create_task(delete_message_after_delay(context, chat_id, sent_message.message_id, delay=600))
    else:
        await update.message.reply_text("❌ Invalid or expired link.")

# --- BACKGROUND TASK: Auto-Delete ---
async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay) # Wait for 600 seconds (10 minutes)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        # Optional: Send a notification that the video cleared
        await context.bot.send_message(chat_id=chat_id, text="⏱️ Time's up! The video has been cleared.")
    except Exception as e:
        print(f"Failed to delete message: {e}")

# --- MAIN ENGINE ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO & filters.Chat(ADMIN_ID), handle_admin_video))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
