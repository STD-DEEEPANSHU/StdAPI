"""
========================================================================
StdAPI 2.3.0 — The Unified Open-Source API Platform
Universal Media Extraction Engine, AI Orchestration, Web Search & Automation
Engineered by STD-DEEPANSHU (github.com/STD-DEEPANSHU) under TeamStdNetwork
========================================================================
"""
import sys

__version__ = "2.3.0"
__author__ = "STD-DEEPANSHU"
__license__ = "LGPL-3.0-or-later"

# Local Embedded Engine
from .extractors.registry import find_extractor, AVAILABLE_EXTRACTORS
from .core.stealth import StealthSession
from .core.ffmpeg import FFmpegPipeline
from .core.cookies import BrowserCookieExtractor
from .core.cache import MediaCache
from .extractors.base import MediaResponse, StreamInfo


class StdEngine:
    """
    High-level local embedded extraction engine (No remote server required).
    Usage:
        import asyncio
        from stdapi import StdEngine

        async def main():
            engine = StdEngine()
            media = await engine.extract("https://www.instagram.com/reel/xyz")
            print(media.best_video_url)

        asyncio.run(main())
    """
    def __init__(self, use_cache: bool = True):
        self.cache = MediaCache() if use_cache else None

    async def extract(self, url: str) -> MediaResponse:
        if self.cache:
            cached = self.cache.get(url)
            if cached:
                streams = [StreamInfo(**s) for s in cached.get("streams", [])]
                cached["streams"] = streams
                return MediaResponse(**cached)

        extractor = find_extractor(url)
        if not extractor:
            raise ValueError(f"Unsupported media URL: {url}")

        result = await extractor.extract(url)

        if self.cache:
            self.cache.set(url, result.to_dict())

        return result


# Core Client & Modules
from .client import StdAPIClient
from .media import MediaModule
from .tools import ToolsModule
from .ai import AIModule, AISession
from .search import SearchModule
from .agent import AgentModule, StdAgent
from .nsfw import NSFWModule
from .results import Result
from .exceptions import (
    StdAPIError,
    ConnectionError,
    RateLimitError,
    AuthenticationError,
    MediaExtractionError,
    ContentBlockedError,
    ValidationError,
    NotFoundError,
)

# Developer-friendly alias: from stdapi import StdAPI
StdAPI = StdAPIClient

# Default Async Module Singletons
_default_client = StdAPIClient()
media = MediaModule(_default_client)
tools = ToolsModule(_default_client)
ai = AIModule(_default_client)
search = SearchModule(_default_client)
agent = AgentModule(_default_client)
nsfw = NSFWModule(_default_client)

# Synchronous Bridge
from . import sync
from .sync import SyncStdAPI

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "StdEngine",
    "StdAPI",
    "StdAPIClient",
    "SyncStdAPI",
    "MediaModule",
    "ToolsModule",
    "AIModule",
    "AISession",
    "SearchModule",
    "AgentModule",
    "NSFWModule",
    "StdAgent",
    "Result",
    "StdAPIError",
    "ConnectionError",
    "RateLimitError",
    "AuthenticationError",
    "MediaExtractionError",
    "ContentBlockedError",
    "ValidationError",
    "NotFoundError",
    "media",
    "tools",
    "ai",
    "search",
    "agent",
    "nsfw",
    "sync",
    "find_extractor",
    "AVAILABLE_EXTRACTORS",
    "StealthSession",
    "FFmpegPipeline",
    "BrowserCookieExtractor",
    "MediaCache",
    "MediaResponse",
    "StreamInfo",
]
