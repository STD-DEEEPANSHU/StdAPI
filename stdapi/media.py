"""
StdAPI Media Engine Module
Provides direct stream extraction, in-memory zero-disk buffer streaming (BytesIO),
chunked HTTP piping, and offline fallback extraction.
"""
import os
from io import BytesIO
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, Callable, AsyncGenerator

from .client import StdAPIClient
from .results import Result
from .exceptions import MediaExtractionError, StdAPIError


class MediaModule:
    """
    Universal media extraction, streaming, and audio conversion engine.
    Designed for Telegram bots, Discord bots, and high-throughput microservices.
    """
    def __init__(self, client: StdAPIClient):
        self.client = client
        self._local_engine = None

    def _get_local_engine(self):
        if self._local_engine is None:
            from . import StdEngine
            self._local_engine = StdEngine()
        return self._local_engine

    async def info(self, url: str) -> Result:
        """
        Extract media metadata (title, thumbnail, duration, uploader, description, formats).
        Tries remote cloud gateway first, falls back to local engine if gateway is offline.
        """
        try:
            return await self.client._request("GET", "/v1/media/analyze", params={"url": url})
        except Exception:
            # Resilient fallback to local StdEngine
            engine = self._get_local_engine()
            res = await engine.extract(url)
            return Result(res.to_dict())

    async def download(
        self,
        url: str,
        format: str = "mp4",
        mode: Optional[str] = None,
        quality: Optional[str] = None
    ) -> Result:
        """
        Get direct high-speed download link for video (mp4) or audio (mp3).
        Returns Result with .download_url, .title, .duration, .thumbnail, etc.
        """
        effective_mode = mode or ("audio" if format.lower() in ("mp3", "audio", "m4a", "wav") else "video")
        params = {"url": url, "format": format, "mode": effective_mode}
        if quality:
            params["quality"] = quality

        try:
            return await self.client._request("GET", "/v1/media/download", params=params)
        except Exception:
            # Resilient local extraction fallback
            engine = self._get_local_engine()
            res = await engine.extract(url)
            direct_url = res.best_audio_url if effective_mode == "audio" else res.best_video_url
            if not direct_url:
                raise MediaExtractionError(f"No direct stream URL could be resolved for: {url}")
            return Result({
                "success": True,
                "title": res.title,
                "url": url,
                "download_url": direct_url,
                "format": format,
                "duration": res.duration,
                "thumbnail": res.thumbnail,
                "author": res.author,
                "extractor": res.extractor
            })

    async def get_buffer(
        self,
        url: str,
        format: str = "mp4",
        mode: Optional[str] = None,
        quality: Optional[str] = None
    ) -> BytesIO:
        """
        Download media directly into an in-memory BytesIO buffer (Zero-Disk I/O).
        Perfect for Telegram (StdGram/Pyrogram reply_video) and Discord bots.
        """
        data = await self.download(url, format=format, mode=mode, quality=quality)
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
            raise MediaExtractionError(f"No direct stream URL returned by media extractor for: {url}")

        session = await self.client.get_session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        async with session.get(download_url, headers=headers) as resp:
            if not resp.ok:
                raise MediaExtractionError(f"Stream server returned status {resp.status} for media: {url}")
            content = await resp.read()
            buf = BytesIO(content)
            title = data.get("title", "media")
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip()[:30]
            buf.name = f"{safe_title or 'media'}.{format}"
            return buf

    async def stream(
        self,
        url: str,
        chunk_size: int = 65536,
        format: str = "mp4"
    ) -> AsyncGenerator[bytes, None]:
        """
        Yields raw binary chunks directly from stream URL for continuous streaming
        in FastAPI (StreamingResponse) or chunked pipe transfers.
        """
        data = await self.download(url, format=format)
        download_url = getattr(data, "download_url", None) or data.get("download_url")
        if not download_url:
            raise MediaExtractionError(f"Cannot stream media, no download URL for: {url}")

        session = await self.client.get_session()
        async with session.get(download_url) as resp:
            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk

    async def download_to_file(
        self,
        url: str,
        output_path: str,
        format: str = "mp4",
        on_progress: Optional[Callable[[int, int, float], None]] = None
    ) -> str:
        """
        Download media directly to local filesystem with progress callback.
        on_progress signature: callback(downloaded_bytes, total_bytes, percent)
        """
        data = await self.download(url, format=format)
        download_url = getattr(data, "download_url", None) or data.get("download_url")
        if not download_url:
            raise MediaExtractionError(f"Cannot download to file, no URL for: {url}")

        session = await self.client.get_session()
        async with session.get(download_url) as resp:
            total_size = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(output_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if on_progress:
                        pct = round((downloaded / total_size * 100), 2) if total_size > 0 else 0.0
                        on_progress(downloaded, total_size, pct)

        return output_path

    async def batch_download(
        self,
        urls: List[str],
        format: str = "mp4",
        max_concurrent: int = 3
    ) -> List[Result]:
        """
        Concurrent extraction and downloading for a list of URLs with concurrency limit.
        """
        sem = asyncio.Semaphore(max_concurrent)

        async def worker(u: str):
            async with sem:
                try:
                    return await self.download(u, format=format)
                except Exception as e:
                    return Result({"success": False, "url": u, "error": str(e)})

        return await asyncio.gather(*(worker(u) for u in urls))

    # Synchronous conveniences
    def download_sync(self, url: str, format: str = "mp4", mode: Optional[str] = None) -> Result:
        from .sync import run_sync
        return run_sync(self.download(url, format=format, mode=mode))

    def get_buffer_sync(self, url: str, format: str = "mp4", mode: Optional[str] = None) -> BytesIO:
        from .sync import run_sync
        return run_sync(self.get_buffer(url, format=format, mode=mode))
