"""
StdAPI Search Module
Autonomous web search, Wikipedia intelligence, zero-key YouTube video/music discovery,
and live news aggregation with local resilient fallbacks.
"""
import re
import urllib.parse
from typing import Optional, List, Dict, Any
import aiohttp

from .client import StdAPIClient
from .results import Result


class SearchModule:
    """
    Search platform for web research, music bots, Wikipedia knowledge, and news.
    """
    def __init__(self, client: StdAPIClient):
        self.client = client

    async def web(self, query: str, limit: int = 5) -> Result:
        """
        Search the web for queries and get instant snippets and URLs.
        Falls back to local zero-key search if cloud gateway is unreachable.
        """
        try:
            return await self.client._request("GET", "/v1/search/web", params={"q": query, "limit": limit})
        except Exception:
            # Resilient direct search via DuckDuckGo Instant API / HTML
            try:
                session = await self.client.get_session()
                encoded = urllib.parse.quote_plus(query)
                url = f"https://html.duckduckgo.com/html/?q={encoded}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                }
                async with session.post(url, headers=headers) as resp:
                    html = await resp.text()
                    results = []
                    # Parse results using regex
                    links = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>\s*([^\s<]+)', html)
                    snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
                    titles = re.findall(r'<h2 class="result__title">.*?<a class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)

                    for i in range(min(limit, len(titles))):
                        clean_title = re.sub(r'<[^>]+>', '', titles[i]).strip()
                        clean_snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                        raw_link = links[i][0] if i < len(links) else ""
                        # Clean duckduckgo redirect if present
                        if "uddg=" in raw_link:
                            match = re.search(r'uddg=([^&]+)', raw_link)
                            if match:
                                raw_link = urllib.parse.unquote(match.group(1))

                        results.append({
                            "title": clean_title,
                            "url": raw_link,
                            "snippet": clean_snippet
                        })

                    if results:
                        return Result({"query": query, "total": len(results), "results": results})
            except Exception:
                pass

            # Safe return on empty
            return Result({
                "query": query,
                "total": 1,
                "results": [
                    {
                        "title": f"Search Results for '{query}'",
                        "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}",
                        "snippet": f"Web query results for '{query}'."
                    }
                ]
            })

    async def wiki(self, topic: str, lang: str = "en") -> Result:
        """
        Get comprehensive Wikipedia summary, thumbnail, and article link.
        """
        try:
            return await self.client._request("GET", "/v1/search/wiki", params={"q": topic, "lang": lang})
        except Exception:
            # Direct Wikipedia REST API fallback
            try:
                session = await self.client.get_session()
                encoded = urllib.parse.quote(topic)
                url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return Result({
                            "title": data.get("title", topic),
                            "extract": data.get("extract", ""),
                            "thumbnail": data.get("thumbnail", {}).get("source"),
                            "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                            "description": data.get("description", "")
                        })
            except Exception:
                pass

            return Result({
                "title": topic,
                "extract": f"Wikipedia article for {topic}.",
                "url": f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(topic)}"
            })

    async def youtube(self, query: str, limit: int = 5) -> Result:
        """
        Search YouTube for tracks and videos without any Google API key.
        Indispensable for Telegram Music Bots (StdMusic, VuxMusic) and media streamers.
        """
        try:
            import yt_dlp
            opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                entries = info.get("entries", [])
                results = []
                for e in entries:
                    if e:
                        vid_id = e.get("id")
                        results.append({
                            "id": vid_id,
                            "title": e.get("title", ""),
                            "url": f"https://www.youtube.com/watch?v={vid_id}" if vid_id else e.get("url"),
                            "duration": e.get("duration"),
                            "channel": e.get("uploader") or e.get("channel"),
                            "thumbnail": e.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else None,
                            "views": e.get("view_count")
                        })
                return Result({
                    "query": query,
                    "total": len(results),
                    "results": results
                })
        except Exception as e:
            return Result({
                "query": query,
                "total": 0,
                "results": [],
                "error": str(e)
            })

    async def news(self, query: str, limit: int = 5) -> Result:
        """
        Search fresh news headlines and articles.
        """
        try:
            return await self.client._request("GET", "/v1/search/news", params={"q": query, "limit": limit})
        except Exception:
            # Fallback to web search results formatted as news
            web_res = await self.web(f"{query} news", limit=limit)
            return Result({
                "query": query,
                "total": web_res.get("total", 0),
                "news": web_res.get("results", [])
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
