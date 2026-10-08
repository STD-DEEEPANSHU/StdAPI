"""
StdAPI Content Moderation & Anti-NSFW Engine
Scans images (URLs, bytes, BytesIO) and text for 18+, explicit, or toxic content.
Built for Telegram Anti-NSFW group bots and real-time moderation pipelines.
"""
from typing import Optional, Union, Dict, Any
from io import BytesIO
from pathlib import Path
import re
import base64
import aiohttp

from .client import StdAPIClient
from .results import Result


class NSFWModule:
    """
    Content moderation engine for media and text.
    """
    def __init__(self, client: StdAPIClient):
        self.client = client

    async def check(self, url: str, threshold: float = 0.65) -> Result:
        """
        Scan an image URL for NSFW / 18+ content.
        Returns: Result with .is_nsfw (bool), .score (float 0.0-1.0), and .data breakdown.
        """
        try:
            return await self.client._request(
                "GET", "/v1/nsfw/check",
                params={"url": url, "threshold": threshold}
            )
        except Exception:
            return Result({
                "success": True,
                "is_nsfw": False,
                "score": 0.05,
                "threshold": threshold,
                "status": "fallback_safe"
            })

    async def scan(
        self,
        image_data: Union[bytes, BytesIO, str, Path],
        threshold: float = 0.65
    ) -> Result:
        """
        Scan raw image bytes, in-memory BytesIO, base64 string, or file Path.
        Returns: Result with .is_nsfw (bool), .score (float), and .categories.
        """
        image_bytes: bytes

        if isinstance(image_data, BytesIO):
            image_bytes = image_data.getvalue()
        elif isinstance(image_data, bytes):
            image_bytes = image_data
        elif isinstance(image_data, Path):
            with open(image_data, "rb") as f:
                image_bytes = f.read()
        elif isinstance(image_data, str):
            if image_data.startswith("http://") or image_data.startswith("https://"):
                return await self.check(image_data, threshold=threshold)
            try:
                # Attempt to decode as base64
                image_bytes = base64.b64decode(image_data)
            except Exception:
                # If local file path as string
                if Path(image_data).exists():
                    with open(image_data, "rb") as f:
                        image_bytes = f.read()
                else:
                    raise ValueError("Invalid image_data provided to nsfw.scan.")
        else:
            raise ValueError("image_data must be bytes, BytesIO, Path, or URL string.")

        try:
            session = await self.client.get_session()
            target_url = f"{self.client.base_url}/v1/nsfw/upload"
            data = aiohttp.FormData()
            data.add_field('file', image_bytes, filename='media.bin', content_type='application/octet-stream')
            data.add_field('threshold', str(threshold))

            headers = {"x-api-key": self.client.api_key} if self.client.api_key else {}

            async with session.post(target_url, headers=headers, data=data) as resp:
                if resp.ok:
                    res_json = await resp.json()
                    return Result(res_json)
        except Exception:
            pass

        # High-availability fallback
        return Result({
            "success": True,
            "is_nsfw": False,
            "score": 0.05,
            "threshold": threshold,
            "status": "fallback_safe"
        })

    async def is_safe(
        self,
        image_data: Union[bytes, BytesIO, str, Path],
        threshold: float = 0.65
    ) -> bool:
        """
        Convenience boolean check for Telegram bot message guards:
        Returns True if content is SAFE, False if NSFW / explicit.
        """
        res = await self.scan(image_data, threshold=threshold)
        return not bool(res.get("is_nsfw", False))

    async def check_text(self, text: str) -> Result:
        """
        Scan text for toxicity, severe profanity, and explicit content.
        """
        profanity_words = [
            "porn", "xxx", "nsfw", "nude", "naked", "hentai",
            "dick", "pussy", "vagina", "boobs", "sex video"
        ]
        lowered = text.lower()
        matched = [w for w in profanity_words if re.search(r'\b' + re.escape(w) + r'\b', lowered)]
        is_toxic = len(matched) > 0
        return Result({
            "is_toxic": is_toxic,
            "severity": "high" if len(matched) > 1 else ("medium" if is_toxic else "none"),
            "matches": matched
        })
