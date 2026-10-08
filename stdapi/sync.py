"""
StdAPI Synchronous Bridge
Enables effortless synchronous execution for scripts, Flask, Django,
Celery tasks, and Jupyter environments without manual asyncio boilerplate.
"""
import asyncio
import threading
from typing import Any, Coroutine, Optional, Dict
from io import BytesIO

from .client import StdAPIClient
from .results import Result


class _LoopWorker:
    """Persistent background event loop running in a dedicated thread."""
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def get_loop(self) -> asyncio.AbstractEventLoop:
        with self._lock:
            if self._loop is None or not self._thread.is_alive():
                self._loop = asyncio.new_event_loop()
                self._thread = threading.Thread(target=self._run_loop, args=(self._loop,), daemon=True)
                self._thread.start()
            return self._loop

    def _run_loop(self, loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def run(self, coro: Coroutine) -> Any:
        loop = self.get_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()


_worker = _LoopWorker()


def run_sync(coro: Coroutine) -> Any:
    """Safely executes an async coroutine synchronously."""
    try:
        # Check if we are inside a running loop
        asyncio.get_running_loop()
        # In a running loop: run via worker thread to avoid collision
        return _worker.run(coro)
    except RuntimeError:
        # No running event loop: can also use worker
        return _worker.run(coro)


class SyncMediaModule:
    def __init__(self, async_media):
        self._async = async_media

    def info(self, url: str) -> Result:
        return run_sync(self._async.info(url))

    def download(self, url: str, format: str = "mp4", mode: Optional[str] = None) -> Result:
        return run_sync(self._async.download(url, format=format, mode=mode))

    def get_buffer(self, url: str, format: str = "mp4", mode: Optional[str] = None) -> BytesIO:
        return run_sync(self._async.get_buffer(url, format=format, mode=mode))

    def download_to_file(self, url: str, output_path: str, format: str = "mp4") -> str:
        return run_sync(self._async.download_to_file(url, output_path, format=format))


class SyncAIModule:
    def __init__(self, async_ai):
        self._async = async_ai

    def chat(self, prompt: str, model: str = "gpt-4o-mini", system_prompt: Optional[str] = None, temperature: float = 0.7) -> Result:
        return run_sync(self._async.chat(prompt, model=model, system_prompt=system_prompt, temperature=temperature))

    def code(self, task: str, language: str = "python") -> Result:
        return run_sync(self._async.code(task, language=language))


class SyncSearchModule:
    def __init__(self, async_search):
        self._async = async_search

    def web(self, query: str, limit: int = 5) -> Result:
        return run_sync(self._async.web(query, limit=limit))

    def wiki(self, topic: str, lang: str = "en") -> Result:
        return run_sync(self._async.wiki(topic, lang=lang))

    def youtube(self, query: str, limit: int = 5) -> Result:
        return run_sync(self._async.youtube(query, limit=limit))

    def news(self, query: str, limit: int = 5) -> Result:
        return run_sync(self._async.news(query, limit=limit))


class SyncToolsModule:
    def __init__(self, async_tools):
        self._async = async_tools

    def qr(self, text: str, box_size: int = 10, border: int = 2) -> Result:
        return run_sync(self._async.qr(text, box_size=box_size, border=border))

    def qr_buffer(self, text: str, box_size: int = 10, border: int = 2) -> BytesIO:
        return run_sync(self._async.qr_buffer(text, box_size=box_size, border=border))

    def temp_mail(self) -> Result:
        return run_sync(self._async.temp_mail())

    def temp_mail_inbox(self, login: str, domain: str) -> Result:
        return run_sync(self._async.temp_mail_inbox(login, domain))

    def wait_for_otp(self, login: str, domain: str, timeout: int = 60) -> Result:
        return run_sync(self._async.wait_for_otp(login, domain, timeout=timeout))

    def ip(self, ip_address: Optional[str] = None) -> Result:
        return run_sync(self._async.ip(ip_address))

    def shorten(self, url: str) -> Result:
        return run_sync(self._async.shorten(url))

    def tts(self, text: str, lang: str = "en") -> BytesIO:
        return run_sync(self._async.tts(text, lang=lang))

    def crypto(self, symbol: str = "BTC") -> Result:
        return run_sync(self._async.crypto(symbol))

    def currency(self, amount: float = 1.0, from_curr: str = "USD", to_curr: str = "INR") -> Result:
        return run_sync(self._async.currency(amount=amount, from_curr=from_curr, to_curr=to_curr))

    def lyrics(self, song: str) -> Result:
        return run_sync(self._async.lyrics(song))

    def hash(self, text: str, algo: str = "sha256") -> Result:
        return self._async.hash(text, algo=algo)

    def password(self, length: int = 16, symbols: bool = True, numbers: bool = True) -> str:
        return self._async.password(length=length, symbols=symbols, numbers=numbers)

    def uuid(self) -> str:
        return self._async.uuid()


class SyncNSFWModule:
    def __init__(self, async_nsfw):
        self._async = async_nsfw

    def check(self, url: str, threshold: float = 0.65) -> Result:
        return run_sync(self._async.check(url, threshold=threshold))

    def scan(self, image_data: Any, threshold: float = 0.65) -> Result:
        return run_sync(self._async.scan(image_data, threshold=threshold))

    def is_safe(self, image_data: Any, threshold: float = 0.65) -> bool:
        return run_sync(self._async.is_safe(image_data, threshold=threshold))

    def check_text(self, text: str) -> Result:
        return run_sync(self._async.check_text(text))


class SyncStdAPI:
    """Synchronous client instance for StdAPI."""
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self._client = StdAPIClient(api_key=api_key, base_url=base_url)
        self.media = SyncMediaModule(self._client.media)
        self.ai = SyncAIModule(self._client.ai)
        self.search = SyncSearchModule(self._client.search)
        self.tools = SyncToolsModule(self._client.tools)
        self.nsfw = SyncNSFWModule(self._client.nsfw)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        run_sync(self._client.close())


_default_sync_client = SyncStdAPI()
media = _default_sync_client.media
ai = _default_sync_client.ai
search = _default_sync_client.search
tools = _default_sync_client.tools
nsfw = _default_sync_client.nsfw
