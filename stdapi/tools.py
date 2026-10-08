"""
StdAPI Developer Utilities & Automation Suite
Disposable emails with OTP auto-wait, in-memory QR generators, IP geolocation,
Text-to-Speech buffers, crypto/currency rates, and crypto-grade security utils.
Powered securely by the central StdAPI Master Gateway.
"""
import re
import os
import io
import base64
import secrets
import string
import hashlib
import uuid
import asyncio
import urllib.parse
from io import BytesIO
from typing import Optional, Dict, Any, List
import aiohttp

from .client import StdAPIClient
from .results import Result
from .exceptions import StdAPIError


class ToolsModule:
    """
    Developer utilities, bot helpers, and automation tools.
    All external lookups and processing are securely handled by the central StdAPI platform.
    """
    def __init__(self, client: StdAPIClient):
        self.client = client

    # ==================== TEMP MAIL & OTP ====================
    async def temp_mail(self) -> Result:
        """
        Generate a random active disposable email address via StdAPI.
        """
        return await self.client._request("GET", "/v1/tools/temp-mail")

    async def temp_mail_inbox(self, login: str, domain: str) -> Result:
        """
        Fetch incoming emails and OTPs for a given temp mail mailbox via StdAPI.
        """
        return await self.client._request(
            "GET", "/v1/tools/temp-mail/inbox",
            params={"login": login, "domain": domain}
        )

    async def temp_mail_message(self, login: str, domain: str, message_id: int) -> Result:
        """
        Fetch full email content by message id via StdAPI.
        """
        return await self.client._request(
            "GET", "/v1/tools/temp-mail/message",
            params={"login": login, "domain": domain, "id": message_id}
        )

    async def wait_for_otp(
        self,
        login: str,
        domain: str,
        timeout: int = 60,
        interval: int = 2,
        code_regex: str = r"\b\d{4,8}\b"
    ) -> Result:
        """
        Autonomous OTP poller! Polls inbox every 2 seconds until a verification code arrives.
        Returns Result with .otp_code, .subject, and .full_message.
        """
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            inbox = await self.temp_mail_inbox(login, domain)
            messages = inbox.get("messages", [])
            if messages:
                latest = messages[0]
                msg_id = latest.get("id")
                subject = latest.get("subject", "")
                body = ""
                try:
                    full_msg = await self.temp_mail_message(login, domain, msg_id)
                    body = full_msg.get("text_body") or full_msg.get("body") or ""
                except Exception:
                    body = ""

                text_to_search = f"{subject} {body}"
                match = re.search(code_regex, text_to_search)
                otp_code = match.group(0) if match else None

                return Result({
                    "success": True,
                    "otp_code": otp_code,
                    "subject": subject,
                    "sender": latest.get("from"),
                    "date": latest.get("date"),
                    "body": body
                })

            await asyncio.sleep(interval)

        return Result({
            "success": False,
            "error": f"Timed out waiting for OTP after {timeout} seconds.",
            "otp_code": None
        })

    # ==================== QR CODE ====================
    async def qr(self, text: str, box_size: int = 10, border: int = 2) -> Result:
        """
        Generate a QR code image as Base64 data URL.
        """
        try:
            return await self.client._request(
                "POST", "/v1/tools/qrcode",
                json={"text": text, "box_size": box_size, "border": border}
            )
        except Exception:
            # Pure local offline generation if qrcode package is present
            try:
                import qrcode
                qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
                qr.add_data(text)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                return Result({
                    "success": True,
                    "text": text,
                    "data_url": f"data:image/png;base64,{b64}"
                })
            except Exception as e:
                return Result({"success": False, "text": text, "error": str(e)})

    async def qr_buffer(self, text: str, box_size: int = 10, border: int = 2) -> BytesIO:
        """
        Generate in-memory BytesIO PNG buffer for QR code.
        Ready to be passed directly to Telegram bot (reply_photo) or Discord!
        """
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.name = "qrcode.png"
            buf.seek(0)
            return buf
        except Exception:
            res = await self.qr(text, box_size=box_size, border=border)
            data_url = res.get("data_url", "")
            if "," in data_url:
                raw_bytes = base64.b64decode(data_url.split(",", 1)[1])
                buf = BytesIO(raw_bytes)
                buf.name = "qrcode.png"
                return buf
            raise StdAPIError("Unable to synthesize QR code buffer.")

    # ==================== IP GEOLOCATION ====================
    async def ip(self, ip_address: Optional[str] = None) -> Result:
        """
        Lookup IP geolocation and network details (city, country, ISP, org, timezone).
        """
        params = {"ip": ip_address} if ip_address else {}
        return await self.client._request("GET", "/v1/tools/ip-lookup", params=params)

    # ==================== TEXT TO SPEECH (TTS) ====================
    async def tts(self, text: str, lang: str = "en") -> BytesIO:
        """
        High-speed Text-to-Speech in-memory BytesIO buffer (MP3).
        Ready to be sent as voice note or audio in Telegram bots or Discord!
        """
        session = await self.client.get_session()
        tts_url = f"{self.client.base_url}/v1/tools/tts"
        params = {"text": text[:300], "lang": lang}
        async with session.get(tts_url, params=params) as resp:
            if not resp.ok:
                raise StdAPIError(f"TTS synthesis failed with status {resp.status}")
            content = await resp.read()
            buf = BytesIO(content)
            buf.name = "voice.mp3"
            return buf

    # ==================== SHORTEN / UNSHORTEN ====================
    async def shorten(self, url: str) -> Result:
        """Shorten long URLs into clean links."""
        return await self.client._request("GET", "/v1/tools/shorten", params={"url": url})

    async def unshorten(self, url: str) -> Result:
        """Follow redirects to reveal the canonical destination URL."""
        session = await self.client.get_session()
        try:
            async with session.head(url, allow_redirects=True) as resp:
                return Result({"success": True, "original_url": url, "destination_url": str(resp.url)})
        except Exception as e:
            return Result({"success": False, "original_url": url, "destination_url": url, "error": str(e)})

    # ==================== CRYPTO & CURRENCY ====================
    async def crypto(self, symbol: str = "BTC") -> Result:
        """Get live cryptocurrency pricing (USD, INR, 24h change) via StdAPI."""
        return await self.client._request("GET", "/v1/tools/crypto", params={"symbol": symbol})

    async def currency(self, amount: float = 1.0, from_curr: str = "USD", to_curr: str = "INR") -> Result:
        """Calculate real-time currency conversions via StdAPI."""
        return await self.client._request(
            "GET", "/v1/tools/currency",
            params={"amount": amount, "from": from_curr, "to": to_curr}
        )

    # ==================== LYRICS ====================
    async def lyrics(self, song: str) -> Result:
        """Find song lyrics and cover art."""
        return await self.client._request("GET", "/v1/tools/lyrics", params={"song": song})

    # ==================== CRYPTOGRAPHIC & SECURITY UTILS (Pure Local) ====================
    @staticmethod
    def hash(text: str, algo: str = "sha256") -> Result:
        """Compute cryptographic hash (md5, sha1, sha256, sha512)."""
        algo_lower = algo.lower()
        encoded = text.encode("utf-8")
        if algo_lower == "md5":
            digest = hashlib.md5(encoded).hexdigest()
        elif algo_lower == "sha1":
            digest = hashlib.sha1(encoded).hexdigest()
        elif algo_lower == "sha512":
            digest = hashlib.sha512(encoded).hexdigest()
        else:
            digest = hashlib.sha256(encoded).hexdigest()
        return Result({"algorithm": algo_lower, "text": text, "digest": digest})

    @staticmethod
    def password(length: int = 16, symbols: bool = True, numbers: bool = True) -> str:
        """Generate cryptographically secure random password."""
        chars = string.ascii_letters
        if numbers:
            chars += string.digits
        if symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        return "".join(secrets.choice(chars) for _ in range(max(8, length)))

    @staticmethod
    def uuid() -> str:
        """Generate a random UUID4 string."""
        return str(uuid.uuid4())
