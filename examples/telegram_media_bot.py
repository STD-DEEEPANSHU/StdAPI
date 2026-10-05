"""
Telegram Media Downloader Bot using StdAPI and StdGram (or Pyrogram).
Downloads Instagram Reels, YouTube Videos/Shorts, TikTok, Twitter/X, and Pinterest
and sends them directly to users via Zero-Disk In-Memory streaming.
"""
import os
import asyncio
from stdapi import media
try:
    from stdgram import Client, filters
    from stdgram.types import Message
except ImportError:
    from pyrogram import Client, filters
    from pyrogram.types import Message

API_ID = int(os.getenv("API_ID", "1234567"))
API_HASH = os.getenv("API_HASH", "your_api_hash_here")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

app = Client("StdMediaBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "👋 **Welcome to StdMedia Downloader Bot!**\n\n"
        "Send me any link from **Instagram, YouTube, TikTok, Twitter/X, or Pinterest**, "
        "and I will send you the media instantly."
    )


@app.on_message(filters.regex(r"https?://[^\s]+"))
async def media_handler(client: Client, message: Message):
    url = message.matches[0].group(0)
    status_msg = await message.reply_text("⚡ *Processing link with StdAPI...*")

    try:
        # 1. Extract metadata
        info = await media.info(url)
        title = info.get("title", "Media")
        duration = info.get("duration", 0)

        await status_msg.edit_text(f"📥 *Downloading:* `{title[:40]}`...")

        # 2. Fetch direct stream into in-memory buffer (Zero disk I/O)
        buf = await media.get_buffer(url, format="mp4")

        await status_msg.edit_text("📤 *Uploading to Telegram...*")

        # 3. Send video directly to user
        await message.reply_video(
            video=buf,
            caption=f"🎬 **{title}**\n\n⚡ *Powered by [StdAPI](https://github.com/STD-DEEPANSHU/StdAPI)*",
            duration=int(duration or 0),
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ *Extraction Failed:* `{e}`")


if __name__ == "__main__":
    print("[*] Starting StdMedia Downloader Bot...")
    app.run()
