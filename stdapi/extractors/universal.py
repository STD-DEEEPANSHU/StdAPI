import re
import yt_dlp
from typing import Optional
from .base import BaseExtractor, MediaResponse, StreamInfo


class UniversalExtractor(BaseExtractor):
    """
    Universal fallback extractor powered by yt-dlp.
    Handles any video/audio URL across 1000+ supported platforms
    with client spoofing and anti-bot mitigation.
    """
    NAME = "Universal"
    VALID_URL = r"^https?://.+"

    async def extract(self, url: str) -> MediaResponse:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "socket_timeout": 30,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
            },
        }

        # Mobile client spoofing if targeting YouTube
        if any(d in url.lower() for d in ("youtube.com", "youtu.be")):
            opts["extractor_args"] = {
                "youtube": {
                    "player_client": ["android", "ios", "web_embedded"]
                }
            }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            streams = []
            for f in info.get("formats", []):
                if f.get("url"):
                    streams.append(
                        StreamInfo(
                            url=f["url"],
                            format=f.get("ext", "mp4"),
                            quality=f.get("format_note") or f"{f.get('height', 'unknown')}p",
                            filesize=f.get("filesize") or f.get("filesize_approx"),
                            has_audio=f.get("acodec") != "none",
                            has_video=f.get("vcodec") != "none",
                        )
                    )

            if not streams and info.get("url"):
                streams.append(StreamInfo(url=info["url"], format=info.get("ext", "mp4")))

            return MediaResponse(
                extractor=info.get("extractor_key") or self.NAME,
                id=str(info.get("id", "media")),
                title=info.get("title") or "Media Stream",
                url=url,
                duration=info.get("duration"),
                thumbnail=info.get("thumbnail"),
                author=info.get("uploader") or info.get("channel"),
                streams=streams,
                description=(info.get("description") or "")[:300],
                metadata={
                    "view_count": info.get("view_count"),
                    "like_count": info.get("like_count"),
                }
            )
