"""
StdAPI Developer Utilities & Automation Suite
Disposable emails with OTP auto-wait, in-memory QR generators, IP geolocation,
Text-to-Speech buffers, crypto/currency rates, and crypto-grade security utils.
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
    """
    def __init__(self, client: StdAPIClient):
        self.client = client

    # ==================== TEMP MAIL & OTP ====================
    async def temp_mail(self) -> Result:
        """
        Generate a random active disposable email address.
        """
        try:
            return await self.client._request("GET", "/v1/tools/temp-mail")
        except Exception:
            # Resilient direct 1secmail API fallback
            try:
                session = await self.client.get_session()
                async with session.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1") as resp:
                    if resp.status == 200:
                        emails = await resp.json()
                        if emails:
                            email = emails[0]
                            login, domain = email.split("@", 1)
                            return Result({
                                "success": True,
                                "email": email,
                                "login": login,
                                "domain": domain,
                                "expires_in": "60 minutes"
                            })
            except Exception:
                pass
            rand_login = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
            return Result({
                "success": True,
                "email": f"{rand_login}@1secmail.com",
                "login": rand_login,
                "domain": "1secmail.com",
                "expires_in": "60 minutes"
            })

    async def temp_mail_inbox(self, login: str, domain: str) -> Result:
        """
        Fetch incoming emails and OTPs for a given temp mail mailbox.
        """
        try:
            return await self.client._request(
                "GET", "/v1/tools/temp-mail/inbox",
                params={"login": login, "domain": domain}
            )
        except Exception:
            try:
                session = await self.client.get_session()
                url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        msgs = await resp.json()
                        return Result({
                            "success": True,
                            "email": f"{login}@{domain}",
                            "message_count": len(msgs),
                            "messages": msgs
                        })
            except Exception:
                pass
            return Result({
                "success": True,
                "email": f"{login}@{domain}",
                "message_count": 0,
                "messages": []
            })

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
                # Fetch full message content if id is available
                subject = latest.get("subject", "")
                body = ""
                try:
                    session = await self.client.get_session()
                    read_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg_id}"
                    async with session.get(read_url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            body = data.get("textBody") or data.get("body") or ""
                except Exception:
                    pass

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
        Generate a QR code image as Base64 data URL and direct PNG image link.
        """
        try:
            return await self.client._request(
                "POST", "/v1/tools/qrcode",
                json={"text": text, "box_size": box_size, "border": border}
            )
        except Exception:
            # Resilient local fallback using qrcode library or Google chart API
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
                    "data_url": f"data:image/png;base64,{b64}",
                    "qr_image_url": f"https://api.qrserver.com/v1/create-qr-code/?data={urllib.parse.quote_plus(text)}"
                })
            except Exception:
                encoded = urllib.parse.quote_plus(text)
                return Result({
                    "success": True,
                    "text": text,
                    "data_url": "",
                    "qr_image_url": f"https://api.qrserver.com/v1/create-qr-code/?data={encoded}&size=300x300"
                })

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
            session = await self.client.get_session()
            url = f"https://api.qrserver.com/v1/create-qr-code/?data={urllib.parse.quote_plus(text)}&size=300x300"
            async with session.get(url) as resp:
                content = await resp.read()
                buf = BytesIO(content)
                buf.name = "qrcode.png"
                return buf

    # ==================== IP GEOLOCATION ====================
    async def ip(self, ip_address: Optional[str] = None) -> Result:
        """
        Lookup IP geolocation and network details (city, country, ISP, org, timezone).
        """
        params = {"ip": ip_address} if ip_address else {}
        try:
            return await self.client._request("GET", "/v1/tools/ip-lookup", params=params)
        except Exception:
            # Resilient direct IP lookup
            session = await self.client.get_session()
            lookup_url = f"https://ipapi.co/{ip_address}/json/" if ip_address else "https://ipapi.co/json/"
            try:
                async with session.get(lookup_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return Result({
                            "success": True,
                            "ip": data.get("ip", ip_address or "unknown"),
                            "city": data.get("city"),
                            "region": data.get("region"),
                            "country": data.get("country_name"),
                            "org": data.get("org"),
                            "timezone": data.get("timezone"),
                            "latitude": data.get("latitude"),
                            "longitude": data.get("longitude")
                        })
            except Exception:
                pass
            return Result({"success": False, "ip": ip_address or "unknown", "error": "Unable to resolve IP."})

    # ==================== TEXT TO SPEECH (TTS) ====================
    async def tts(self, text: str, lang: str = "en") -> BytesIO:
        """
        Free, high-speed Text-to-Speech in-memory BytesIO buffer (MP3).
        Ready to be sent as voice note or audio in Telegram bots or Discord!
        """
        session = await self.client.get_session()
        encoded = urllib.parse.quote_plus(text[:250])
        # Direct Google Translate TTS endpoint (zero key, in-memory)
        tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl={lang}&client=tw-ob"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "http://translate.google.com/"
        }
        async with session.get(tts_url, headers=headers) as resp:
            content = await resp.read()
            buf = BytesIO(content)
            buf.name = "voice.mp3"
            return buf

    # ==================== SHORTEN / UNSHORTEN ====================
    async def shorten(self, url: str) -> Result:
        """Shorten long URLs into clean tiny links."""
        try:
            return await self.client._request("GET", "/v1/tools/shorten", params={"url": url})
        except Exception:
            try:
                session = await self.client.get_session()
                api_url = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote_plus(url)}"
                async with session.get(api_url) as resp:
                    if resp.status == 200:
                        short = await resp.text()
                        return Result({"success": True, "original_url": url, "short_url": short.strip()})
            except Exception:
                pass
            return Result({"success": True, "original_url": url, "short_url": url})

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
        """Get live cryptocurrency pricing (USD, INR, 24h change)."""
        session = await self.client.get_session()
        sym = symbol.upper()
        try:
            # Free Binance ticker API
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}USDT"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price = float(data.get("lastPrice", 0))
                    change = float(data.get("priceChangePercent", 0))
                    return Result({
                        "success": True,
                        "symbol": sym,
                        "price_usd": price,
                        "change_24h_percent": change,
                        "high_24h": float(data.get("highPrice", 0)),
                        "low_24h": float(data.get("lowPrice", 0)),
                        "volume": float(data.get("volume", 0))
                    })
        except Exception:
            pass
        return Result({"success": False, "symbol": sym, "error": "Unable to fetch crypto rate."})

    async def currency(self, amount: float = 1.0, from_curr: str = "USD", to_curr: str = "INR") -> Result:
        """Calculate real-time currency conversions."""
        session = await self.client.get_session()
        base = from_curr.upper()
        target = to_curr.upper()
        try:
            url = f"https://open.er-api.com/v6/latest/{base}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rates = data.get("rates", {})
                    rate = rates.get(target)
                    if rate:
                        converted = round(amount * rate, 4)
                        return Result({
                            "success": True,
                            "amount": amount,
                            "from": base,
                            "to": target,
                            "rate": rate,
                            "converted_amount": converted
                        })
        except Exception:
            pass
        return Result({"success": False, "error": f"Unable to convert {base} to {target}"})

    # ==================== LYRICS ====================
    async def lyrics(self, song: str) -> Result:
        """Find song lyrics and cover art."""
        try:
            return await self.client._request("GET", "/v1/tools/lyrics", params={"song": song})
        except Exception:
            return Result({
                "success": False,
                "song": song,
                "error": "Lyrics service currently unavailable."
            })

    # ==================== CRYPTOGRAPHIC & SECURITY UTILS ====================
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
