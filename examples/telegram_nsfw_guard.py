"""
Telegram Group Anti-NSFW Moderation Guard using StdAPI and StdGram / Pyrogram.
Automatically intercepts incoming media (photos, stickers, video thumbnails),
scans them via StdAPI NSFW moderation engine, and deletes pornographic content.
"""
import os
import asyncio
from io import BytesIO
from stdapi import nsfw
try:
    from stdgram import Client, filters
    from stdgram.types import Message
except ImportError:
    from pyrogram import Client, filters
    from pyrogram.types import Message

API_ID = int(os.getenv("API_ID", "1234567"))
API_HASH = os.getenv("API_HASH", "your_api_hash_here")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

app = Client("StdNSFWGuardBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.group & (filters.photo | filters.sticker | filters.animation))
async def nsfw_filter_handler(client: Client, message: Message):
    try:
        # Download media file into memory
        file_buffer = await client.download_media(message, in_memory=True)
        if not file_buffer:
            return

        # Scan with StdAPI NSFW detection engine (threshold: 0.65)
        scan_result = await nsfw.scan(file_buffer, threshold=0.65)

        if scan_result.get("is_nsfw"):
            # Delete explicit message immediately
            await message.delete()

            user_mention = message.from_user.mention if message.from_user else "User"
            score = round(scan_result.get("score", 0.99) * 100, 1)

            warn_msg = await message.reply_text(
                f"🚨 **NSFW Warning!**\n\n"
                f"{user_mention}, your media was removed because it contained explicit content "
                f"({score}% confidence).\n\n"
                f"🛡️ *Group Protected by [StdAPI NSFW Engine](https://github.com/STD-DEEPANSHU/StdAPI)*"
            )

            # Auto-clean warning after 10 seconds to keep group tidy
            await asyncio.sleep(10)
            await warn_msg.delete()

    except Exception as e:
        print(f"[!] NSFW Scan Error: {e}")


if __name__ == "__main__":
    print("[*] Starting StdNSFW Group Moderation Guard...")
    app.run()
