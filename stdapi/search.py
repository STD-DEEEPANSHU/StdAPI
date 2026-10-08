"""
StdAPI Search Module
Autonomous web search, Wikipedia intelligence, zero-key YouTube video/music discovery,
and live news aggregation powered by the central StdAPI Master Gateway.
"""
from typing import Optional, List, Dict, Any

from .client import StdAPIClient
from .results import Result


class SearchModule:
    """
    Search platform for web research, music bots, Wikipedia knowledge, and news.
    All search queries are processed securely through the StdAPI Master Gateway.
    """
    def __init__(self, client: StdAPIClient):
        self.client = client

    async def web(self, query: str, limit: int = 5) -> Result:
        """
        Search the web for queries and get instant snippets and URLs via StdAPI Gateway.
        """
        try:
            return await self.client._request("GET", "/v1/search/web", params={"q": query, "limit": limit})
        except Exception as e:
            return Result({
                "query": query,
                "total": 0,
                "results": [],
                "error": str(e)
            })

    async def wiki(self, topic: str, lang: str = "en") -> Result:
        """
        Get comprehensive Wikipedia summary, thumbnail, and article link via StdAPI Gateway.
        """
        try:
            return await self.client._request("GET", "/v1/search/wiki", params={"q": topic, "lang": lang})
        except Exception as e:
            return Result({
                "title": topic,
                "extract": "",
                "error": str(e)
            })

    async def youtube(self, query: str, limit: int = 5) -> Result:
        """
        Search YouTube for tracks and videos without any Google API key.
        Indispensable for Telegram Music Bots (StdMusic, VuxMusic) and media streamers.
        """
        try:
            return await self.client._request("GET", "/v1/search/youtube", params={"q": query, "limit": limit})
        except Exception as e:
            return Result({
                "query": query,
                "total": 0,
                "results": [],
                "error": str(e)
            })

    async def news(self, query: str, limit: int = 5) -> Result:
        """
        Search fresh news headlines and articles via StdAPI Gateway.
        """
        try:
            return await self.client._request("GET", "/v1/search/news", params={"q": query, "limit": limit})
        except Exception as e:
            return Result({
                "query": query,
                "total": 0,
                "news": [],
                "error": str(e)
            })

    # Synchronous conveniences
    def web_sync(self, query: str, limit: int = 5) -> Result:
        from .sync import run_sync
        return run_sync(self.web(query, limit=limit))

    def wiki_sync(self, topic: str, lang: str = "en") -> Result:
        from .sync import run_sync
        return run_sync(self.wiki(topic, lang=lang))

    def youtube_sync(self, query: str, limit: int = 5) -> Result:
        from .sync import run_sync
        return run_sync(self.youtube(query, limit=limit))

    def news_sync(self, query: str, limit: int = 5) -> Result:
        from .sync import run_sync
        return run_sync(self.news(query, limit=limit))
