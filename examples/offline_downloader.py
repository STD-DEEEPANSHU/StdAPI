"""
Offline / Local Media Extractor using StdAPI StdEngine (like yt-dlp).
Does not require any server or internet backend. Runs completely locally on your machine
with stealth browser fingerprint spoofing and FFmpeg transcoding.
"""
import asyncio
from stdapi import StdEngine


async def main():
    # Initialize offline engine (uses local cache & stealth spoofing)
    engine = StdEngine(use_cache=True)

    urls = [
        "https://www.instagram.com/reel/C8xY9zABCDE/",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://twitter.com/example/status/1234567890",
    ]

    for url in urls:
        print(f"\n[*] Extracting: {url}")
        try:
            res = await engine.extract(url)
            print(f"  [✓] Platform:      {res.extractor}")
            print(f"  [✓] Title:         {res.title}")
            print(f"  [✓] Author:        {res.author}")
            print(f"  [✓] Duration:      {res.duration}s")
            print(f"  [✓] Best Video:    {res.best_video_url}")
            print(f"  [✓] Best Audio:    {res.best_audio_url}")
        except Exception as e:
            print(f"  [x] Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
