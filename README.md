# StdAPI

<p align="center">
  <strong>Universal Media Extraction Engine, Developer Utility API & Telegram Bot Toolkit</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/stdapi/"><img src="https://img.shields.io/pypi/v/stdapi?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/stdapi/"><img src="https://img.shields.io/pypi/dm/stdapi?style=flat-square&color=blueviolet" alt="Downloads"></a>
  <a href="https://github.com/STD-DEEPANSHU/StdAPI/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-LGPL--3.0-green?style=flat-square" alt="License"></a>
  <a href="https://github.com/STD-DEEPANSHU/StdAPI/actions"><img src="https://img.shields.io/github/actions/workflow/status/STD-DEEPANSHU/StdAPI/ci.yml?branch=master&style=flat-square" alt="Build"></a>
  <a href="https://github.com/STD-DEEPANSHU/StdAPI"><img src="https://img.shields.io/github/stars/STD-DEEPANSHU/StdAPI?style=flat-square" alt="Stars"></a>
</p>

---

**StdAPI** is an open-source Python library and engine engineered for media downloading, automated content moderation, developer utilities, and AI orchestration. It combines the local extraction capabilities of tools like `yt-dlp` with the convenient cloud API surface of multi-tool services like `SafoneAPI`.

Built specifically with Telegram bots (`StdGram`, `Pyrogram`, `Telethon`), Discord bots, and automated microservices in mind, StdAPI provides native **Zero-Disk In-Memory Streaming** (`get_buffer()`) so bots can forward media directly to users without touching the local disk.

---

## Key Features

- **Dual-Engine Architecture:**
  - **Local Engine (`StdEngine`):** Self-contained extractor running directly on your machine. Employs real TLS/JA3 browser fingerprint spoofing, local cookie extraction (Chrome, Firefox, Edge), and in-process FFmpeg stream muxing to bypass IP throttling and login walls without external servers.
  - **Cloud SDK (`stdapi` Client):** Ultra-fast asynchronous client connecting to high-throughput gateway nodes for media downloads, NSFW filtering, disposable email generation, and AI chat.
- **Universal Media Extraction:** Out-of-the-box support for Instagram Reels/Stories, YouTube, TikTok (without watermark), Twitter/X, Pinterest, plus universal fallback for 1,000+ platforms supported by `yt-dlp`.
- **Zero-Disk Buffer Streaming:** Fetch direct stream bytes into in-memory `io.BytesIO` buffers, eliminating temporary file I/O overhead on bot servers.
- **NSFW Content Scanner:** Scan URLs, in-memory bytes, or base64 strings to filter explicit images in group chats.
- **Developer Utilities:** Temporary disposable email generator with live inbox polling, QR code generation, and IP geolocation lookup.
- **Model Context Protocol (MCP):** Embedded stdio MCP server for Claude Desktop, Cursor, and AI developer workflows.

---

## Installation

```bash
pip install -U stdapi
```

Optional: To enable automated local browser cookie harvesting for protected streams:
```bash
pip install -U "stdapi[cookies]"
```

---

## Quickstart

### 1. Telegram Bot (StdGram / Pyrogram) — Zero-Disk Video Downloader

```python
import os
from stdapi import media
from stdgram import Client, filters

app = Client("MediaBot", api_id=12345, api_hash="your_hash", bot_token="your_token")

@app.on_message(filters.regex(r"https?://[^\s]+"))
async def download_handler(client, message):
    url = message.matches[0].group(0)
    msg = await message.reply_text("Processing link...")

    # Fetch media directly into in-memory buffer without saving to disk
    buf = await media.get_buffer(url, format="mp4")

    await message.reply_video(video=buf, caption="Downloaded via StdAPI")
    await msg.delete()

app.run()
```

### 2. Telegram Group Anti-NSFW Moderation Guard

```python
from stdapi import nsfw
from stdgram import Client, filters

app = Client("NSFWGuard", api_id=12345, api_hash="your_hash", bot_token="your_token")

@app.on_message(filters.group & (filters.photo | filters.sticker))
async def scan_media(client, message):
    media_buf = await client.download_media(message, in_memory=True)
    scan = await nsfw.scan(media_buf, threshold=0.65)

    if scan.get("is_nsfw"):
        await message.delete()
        await message.reply_text("Explicit media removed by StdAPI Guard.")

app.run()
```

### 3. Standalone Offline Extraction (`StdEngine`)

Run locally without any server or remote backend:

```python
import asyncio
from stdapi import StdEngine

async def main():
    engine = StdEngine()
    result = await engine.extract("https://www.instagram.com/reel/Cxxxxxx/")
    
    print(f"Title:        {result.title}")
    print(f"Platform:     {result.extractor}")
    print(f"Direct Stream:{result.best_video_url}")

asyncio.run(main())
```

### 4. Developer Tools (Temp-Mail & IP Lookup)

```python
import asyncio
from stdapi import tools

async def main():
    # 1-Click Disposable Email
    mailbox = await tools.temp_mail()
    print(f"Email: {mailbox.email}")

    # Check Mailbox Inbox for OTPs
    inbox = await tools.temp_mail_inbox(mailbox.login, mailbox.domain)
    print(f"Messages: {inbox.get('messages', [])}")

    # IP Geolocation
    ip_data = await tools.ip()
    print(f"My Server IP: {ip_data.ip} ({ip_data.city}, {ip_data.country})")

asyncio.run(main())
```

---

## Command Line Interface (CLI)

StdAPI includes an interactive command-line utility:

```bash
# Interactive diagnostics dashboard
stdapi tui

# Extract direct stream URL from any media link
stdapi extract "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Convert video to 320kbps MP3
stdapi convert input.mp4 output.mp3

# Clean temporary OS cache
stdapi clean

# Start Model Context Protocol (MCP) server
stdapi mcp
```

---

## Model Context Protocol (MCP) Integration

To use StdAPI with **Claude Desktop** or **Cursor IDE**, add this entry to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "stdapi": {
      "command": "stdapi",
      "args": ["mcp"]
    }
  }
}
```

---

## Comparison

| Feature | StdAPI | yt-dlp | SafoneAPI |
|:---|:---:|:---:|:---:|
| **Local Offline Extractor** | Yes (`StdEngine`) | Yes | No (Cloud Only) |
| **Cloud API Gateway** | Yes (`stdapi.media`) | No | Yes |
| **Zero-Disk In-Memory Buffer** | Yes (`get_buffer`) | Manual | Limited |
| **Telegram Bot Native Support** | Yes (`StdGram`/`Pyrogram`) | Wrapper Needed | Yes |
| **NSFW Moderation Scanner** | Yes (`stdapi.nsfw`) | No | Yes |
| **Temp-Mail & Dev Utilities** | Yes (`stdapi.tools`) | No | Yes |
| **In-Process FFmpeg Transcoding** | Yes | Yes (Subprocess) | No |
| **Model Context Protocol (MCP)** | Yes | No | No |

---

## License & Legal Attribution

StdAPI is licensed under the **GNU Lesser General Public License v3.0 (LGPLv3)**.  
See [LICENSE](LICENSE) and [NOTICE](NOTICE) for the complete legal text and attribution terms.

```
Copyright (C) 2024-2026 STD-DEEPANSHU <stddeepanshu@aol.com>
Engineered by STD-DEEPANSHU under TeamStdNetwork.
```
