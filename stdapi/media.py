from typing import Optional
from io import BytesIO
from .client import StdAPIClient
from .results import Result

class MediaModule:
    def __init__(self, client: StdAPIClient):
        self.client = client

    async def info(self, url: str) -> Result:
        """Extract metadata (title, thumbnail, duration, uploader) from media URL."""
        return await self.client._request("GET", "/v1/media/analyze", params={"url": url})

    async def download(self, url: str, format: str = "mp4", mode: Optional[str] = None) -> Result:
        """
        Get direct high-speed download link for video (mp4) or audio (mp3).
        Works seamlessly in Telegram Music Bots, Discord Bots, and Python apps.
        Returns:
            Result object with .download_url, .file_id (for Telegram bots), .title, .duration, .formats, etc.
        """
        effective_mode = mode or ("audio" if format.lower() in ("mp3", "audio", "m4a") else "video")
        return await self.client._request(
            "GET", 
            "/v1/media/download", 
            params={"url": url, "format": format, "mode": effective_mode}
        )

    async def get_buffer(self, url: str, format: str = "mp4", mode: Optional[str] = None) -> BytesIO:
        """
        Download media directly into an in-memory BytesIO buffer (Zero disk I/O).
        Perfect for Telegram (Pyrogram/StdGram), Discord, and web apps.
        """
        data = await self.download(url, format=format, mode=mode)
        download_url = (
            getattr(data, "download_url", None)
            or data.get("download_url")
            or data.get("url")
        )
        if not download_url:
            streams = data.get("streams", [])
            if streams and isinstance(streams, list) and len(streams) > 0:
                first = streams[0]
                download_url = first.get("url") if isinstance(first, dict) else getattr(first, "url", None)

        if not download_url:
            from .exceptions import StdAPIError
            raise StdAPIError(f"No direct stream URL returned by media extractor for: {url}")

        session = await self.client.get_session()
        async with session.get(download_url) as resp:
            content = await resp.read()
            buf = BytesIO(content)
            title = data.get("title", "media")
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()[:25]
            buf.name = f"{safe_title or 'media'}.{format}"
            return buf

