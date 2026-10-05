from typing import List, Type, Optional
from .base import BaseExtractor
from .instagram import InstagramExtractor
from .youtube import YouTubeExtractor
from .tiktok import TikTokExtractor
from .twitter import TwitterExtractor
from .pinterest import PinterestExtractor
from .universal import UniversalExtractor

AVAILABLE_EXTRACTORS: List[Type[BaseExtractor]] = [
    InstagramExtractor,
    YouTubeExtractor,
    TikTokExtractor,
    TwitterExtractor,
    PinterestExtractor,
]

def find_extractor(url: str) -> Optional[BaseExtractor]:
    """Find and instantiate the matching extractor for a URL."""
    for extractor_cls in AVAILABLE_EXTRACTORS:
        if extractor_cls.matches(url):
            return extractor_cls()
    if url.strip().startswith(("http://", "https://")):
        return UniversalExtractor()
    return None

