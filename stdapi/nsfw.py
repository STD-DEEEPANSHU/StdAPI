from typing import Optional, Union, Dict, Any
from io import BytesIO
from .client import StdAPIClient
from .results import Result


class NSFWModule:
    """
    StdNSFW Content Moderation & 18+ Detection Engine.
    Compatible with VuxMusic and Telegram Anti-NSFW Group Protection bots.
    """

    def __init__(self, client: StdAPIClient):
        self.client = client

    async def check(self, url: str, threshold: float = 0.65) -> Result:
        """
        Scan an image URL for NSFW / 18+ content.
        Returns:
            Result with .is_nsfw (bool), .score (float 0.0 - 1.0), and .data (detailed nudity breakdown).
        """
        return await self.client._request(
            "GET",
            "/v1/nsfw/check",
            params={"url": url, "threshold": threshold}
        )

    async def scan(self, image_data: Union[bytes, BytesIO, str], threshold: float = 0.65) -> Result:
        """
        Scan raw image bytes, in-memory BytesIO, or base64 string for NSFW content.
        Perfect for Telegram Bot on_message media scans (photo, sticker thumb, video thumb).
        """
        if isinstance(image_data, BytesIO):
            image_bytes = image_data.getvalue()
        elif isinstance(image_data, bytes):
            image_bytes = image_data
        elif isinstance(image_data, str):
            if image_data.startswith("http://") or image_data.startswith("https://"):
                return await self.check(image_data, threshold=threshold)
            return await self.client._request(
                "POST",
                "/v1/nsfw/scan",
                json={"image_base64": image_data, "threshold": threshold}
            )
        else:
            raise ValueError("image_data must be bytes, BytesIO, or URL string.")

        # Multipart form upload
        session = await self.client.get_session()
        target_url = f"{self.client.base_url}/v1/nsfw/upload"
        import aiohttp
        data = aiohttp.FormData()
        data.add_field('file', image_bytes, filename='media.bin', content_type='application/octet-stream')
        data.add_field('threshold', str(threshold))

        headers = {"x-api-key": self.client.api_key} if self.client.api_key else {}

        async with session.post(target_url, headers=headers, data=data) as resp:
            res_json = await resp.json()
            return Result(res_json)
