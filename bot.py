import os
import logging
import subprocess
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fetch bot token from environment variable
TOKEN = os.environ.get("BOT_TOKEN")

# Custom Welcome Message
WELCOME_TEXT = (
    "សូមស្វាគមន៍មកកាន់ MP4 Video Converter Bot! 🎥🌟\n\n"
    "សូមផ្ញើវីដេអូ ឬឯកសារវីដេអូមកទីនេះ ដើម្បីបំប្លែងទៅជា MP4 ដោយឥតគិតថ្លៃ និងលឿនរហ័ស!"
)

async def post_init(application):
    """Set bot commands menu on startup."""
    commands = [
        BotCommand("start", "ចាប់ផ្តើមប្រើប្រាស់ និងបង្ហាញព័ត៌មាន (Start Bot)"),
        BotCommand("help", "របៀបប្រើប្រាស់ប៊ុត (How to use)"),
        BotCommand("about", "អំពី SB24 (About SB24)")
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands updated successfully in Telegram menu.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message on /start command."""
    await update.message.reply_text(WELCOME_TEXT)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help instructions."""
    help_text = (
        "ℹ️ **របៀបប្រើប្រាស់:**\n"
        "1. ផ្ញើវីដេអូ ឬឯកសារវីដេអូ (MP4, MKV, AVI, MOV, ផ្សេងៗ) មកកាន់ Bot នេះ\n"
        "2. រង់ចាំ Bot ទាញយក និងបំប្លែងទៅជា MP4\n"
        "3. Bot នឹងផ្ញើវីដេអូ MP4 ត្រឡប់មកវិញដោយស្វ័យប្រវត្តិ!"
    )
    await update.message.reply_markdown(help_text)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send about info."""
    await update.message.reply_text(WELCOME_TEXT)

async def convert_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming video/document files and convert them to MP4."""
    message = update.message
    video_file = message.video or message.document or message.animation

    if not video_file:
        await message.reply_text("សូមផ្ញើឯកសារវីដេអូដែលត្រឹមត្រូវ! (Please send a valid video file)")
        return

    status_msg = await message.reply_text("⏳ កំពុងទាញយក និងបំប្លែងវីដេអូ សូមរង់ចាំ... (Downloading & converting video...)")

    # Local file path definitions
    input_path = f"input_{video_file.file_id}"
    output_path = f"output_{video_file.file_id}.mp4"

    try:
        # Download file from Telegram
        tg_file = await context.bot.get_file(video_file.file_id)
        await tg_file.download_to_drive(input_path)

        # Convert video to MP4 using FFmpeg
        command = [
            "ffmpeg",
            "-y",                   # Overwrite output file if exists
            "-i", input_path,       # Input file
            "-c:v", "libx264",      # Video codec
            "-preset", "fast",      # Speed/quality balance
            "-crf", "23",           # Quality standard
            "-c:a", "aac",          # Audio codec
            "-b:a", "128k",         # Audio bitrate
            output_path
        ]

        # Execute FFmpeg process
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            logger.error(f"FFmpeg error: {process.stderr.decode('utf-8')}")
            await status_msg.edit_text("❌ មានបញ្ហាក្នុងការបំប្លែងវីដេអូ! (Failed to convert video)")
            return

        # Upload converted video back to user
        await status_msg.edit_text("📤 កំពុងផ្ញើវីដេអូដែលបំប្លែងរួច... (Sending converted MP4...)")
        
        with open(output_path, "rb") as video:
            await message.reply_video(
                video=video,
                caption="✅ វីដេអូរបស់អ្នកត្រូវបានបំប្លែងទៅជា MP4 រួចរាល់! 🎉\n\n" + WELCOME_TEXT
            )
            
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await status_msg.edit_text("❌ មានបញ្ហាបានកើតឡើង! (An error occurred while processing.)")

    finally:
        # Clean up local temporary files
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable is missing!")

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO | filters.ANIMATION, convert_video))

    logger.info("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
