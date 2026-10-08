"""
Telegram Music Streamer Bot using StdAPI and StdGram / Pyrogram.
Searches YouTube without any API key, extracts 320kbps MP3 audio,
and sends audio directly to users without saving files to disk.
"""
import os
import asyncio
from stdapi import media, search

try:
    from stdgram import Client, filters
    from stdgram.types import Message
except ImportError:
    from pyrogram import Client, filters
    from pyrogram.types import Message

API_ID = int(os.getenv("API_ID", "1234567"))
API_HASH = os.getenv("API_HASH", "your_api_hash_here")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

app = Client("StdMusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("play") | filters.command("song"))
async def play_handler(client: Client, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        await message.reply_text("❗ **Usage:** `/play <song name or artist>`")
        return

    status = await message.reply_text(f"🔍 *Searching for:* `{query}`...")

    try:
        # 1. Search YouTube tracks without any Google API key
        results = await search.youtube(query, limit=1)
        tracks = results.get("results", [])
        if not tracks:
            await status.edit_text("❌ No tracks found for your query.")
            return

        track = tracks[0]
        title = track.get("title", "Audio Track")
        channel = track.get("channel", "Artist")
        duration = int(track.get("duration") or 0)
        track_url = track.get("url")

        await status.edit_text(f"🎵 *Downloading Audio:* `{title[:40]}`...")

        # 2. Fetch in-memory MP3 buffer (Zero-disk I/O)
        audio_buf = await media.get_buffer(track_url, format="mp3", mode="audio")

        await status.edit_text("📤 *Sending audio file...*")

        # 3. Send audio with proper metadata
        await message.reply_audio(
            audio=audio_buf,
            title=title,
            performer=channel,
            duration=duration,
            caption=f"🎧 **{title}**\n👤 **{channel}**\n\n⚡ *Powered by [StdAPI](https://github.com/STD-DEEPANSHU/StdAPI)*"
        )
        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ *Playback Error:* `{e}`")


if __name__ == "__main__":
    print("[*] Starting StdMusic Bot...")
    app.run()
