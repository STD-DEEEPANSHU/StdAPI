"""
StdAPI Core Asynchronous Client
Provides resilient HTTP networking with connection pooling, automatic retries,
and high-speed streaming capabilities for the StdAPI ecosystem.
"""
import os
import asyncio
import random
import logging
from typing import Optional, Dict, Any, Union
import aiohttp

from .exceptions import (
    StdAPIError, ConnectionError, RateLimitError,
    AuthenticationError, NotFoundError, ValidationError
)
from .results import Result

logger = logging.getLogger("stdapi")
DEFAULT_BASE_URL = os.getenv("STDAPI_BASE_URL", "https://stdapi.vercel.app")


class StdAPIClient:
    """
    High-Performance Asynchronous Client for StdAPI Gateway & Microservices.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        proxy: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None
    ):
        self.api_key = api_key or os.getenv("STDAPI_KEY") or os.getenv("STDAPI_API_KEY")
        self.base_url = (
            base_url
            or os.getenv("STDAPI_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.proxy = proxy or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        self._custom_session = session
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def get_session(self) -> aiohttp.ClientSession:
        """Returns or creates the underlying persistent connection pool session."""
        if self._custom_session and not self._custom_session.closed:
            return self._custom_session
        if self._session is None or self._session.closed:
            headers = {
                "User-Agent": "StdAPI-Python-SDK/2.3.0 (TeamStdNetwork; +https://github.com/STD-DEEPANSHU/StdAPI)",
                "Accept": "application/json"
            }
            if self.api_key:
                headers["x-api-key"] = self.api_key
                headers["Authorization"] = f"Bearer {self.api_key}"

            connector = aiohttp.TCPConnector(
                limit=100,
                keepalive_timeout=60
            )
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout,
                connector=connector
            )
        return self._session

    @property
    def media(self):
        from .media import MediaModule
        return MediaModule(self)

    @property
    def nsfw(self):
        from .nsfw import NSFWModule
        return NSFWModule(self)

    @property
    def tools(self):
        from .tools import ToolsModule
        return ToolsModule(self)

    @property
    def ai(self):
        from .ai import AIModule
        return AIModule(self)

    @property
    def search(self):
        from .search import SearchModule
        return SearchModule(self)

    @property
    def agent(self):
        from .agent import AgentModule
        return AgentModule(self)

    async def close(self):
        """Closes the underlying aiohttp connection session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Result:
        """
        Executes HTTP request with exponential backoff and automatic retry on transient errors.
        """
        session = await self.get_session()
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    data=data,
                    headers=headers,
                    proxy=self.proxy
                ) as resp:
                    if resp.status == 429:
                        if attempt < self.max_retries:
                            backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                            await asyncio.sleep(backoff)
                            continue
                        raise RateLimitError("Rate limit reached on StdAPI server.")

                    if resp.status in (502, 503, 504):
                        if attempt < self.max_retries:
                            backoff = (1.5 ** attempt) + random.uniform(0.5, 1.0)
                            await asyncio.sleep(backoff)
                            continue

                    try:
                        resp_data = await resp.json(content_type=None)
                    except Exception:
                        text = await resp.text()
                        if resp.status == 404:
                            raise NotFoundError(f"Endpoint not found: {path}")
                        raise StdAPIError(f"Server returned non-JSON response ({resp.status}): {text[:150]}", status_code=resp.status)

                    if not resp.ok:
                        detail = resp_data.get("detail") if isinstance(resp_data, dict) else str(resp_data)
                        if resp.status == 401 or resp.status == 403:
                            raise AuthenticationError(f"Auth failed [{resp.status}]: {detail}")
                        elif resp.status == 400:
                            raise ValidationError(f"Validation failed: {detail}")
                        elif resp.status == 404:
                            raise NotFoundError(f"Resource not found: {detail}")
                        raise StdAPIError(f"StdAPI Error [{resp.status}]: {detail}", status_code=resp.status)

                    return Result(resp_data)

            except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError) as e:
                last_error = e
                if attempt < self.max_retries:
                    await asyncio.sleep((1.5 ** attempt) + random.uniform(0.2, 0.8))
                    continue
                raise ConnectionError(f"Could not connect to StdAPI server at {self.base_url}: {e}")
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0)
                    continue
                raise StdAPIError(f"Request timed out for endpoint {path}", status_code=408)

        if last_error:
            raise ConnectionError(f"Connection failed after {self.max_retries} retries: {last_error}")
        raise StdAPIError(f"Request failed for endpoint {path}")
