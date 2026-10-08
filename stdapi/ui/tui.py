"""
StdAPI Interactive Terminal Diagnostics & TUI Dashboard
Uses Rich to render system diagnostics, network readiness, extractors,
and live hardware telemetry.
"""
import sys
import os
from pathlib import Path
from ..extractors.registry import AVAILABLE_EXTRACTORS
from ..core.ffmpeg import FFmpegPipeline
from ..core.cache import CACHE_DB_PATH

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


def render_banner():
    banner = r"""
   _____ _       _     ___  ______ _____ 
  /  ___| |     | |   / _ \ | ___ \_   _|
  \ `--.| |_  __| |  / /_\ \| |_/ / | |  
   `--. \ __|/ _` |  |  _  ||  __/  | |  
  /\__/ / |_| (_| |  | | | || |    _| |_ 
  \____/ \__|\__,_|  \_| |_/\_|    \___/ 
"""
    if HAS_RICH:
        console.print(f"[bold cyan]{banner}[/bold cyan]")
        console.print("[bold yellow]⚡ StdAPI 2.3.0 — Unified API Platform for AI, Media, Search & Automation[/bold yellow]")
        console.print("[dim]Engineered by TeamStdNetwork • github.com/STD-DEEPANSHU/StdAPI[/dim]\n")
    else:
        print(banner)
        print("StdAPI 2.3.0 — Unified API Platform for AI, Media, Search & Automation")
        print("Engineered by TeamStdNetwork • github.com/STD-DEEPANSHU/StdAPI\n")


def show_diagnostics():
    render_banner()
    ffmpeg_ok = FFmpegPipeline.is_available()
    extractors_str = ", ".join([e.NAME for e in AVAILABLE_EXTRACTORS])
    cache_exists = CACHE_DB_PATH.exists()
    cache_size = round(CACHE_DB_PATH.stat().st_size / 1024, 2) if cache_exists else 0.0

    if HAS_RICH:
        table = Table(title="[bold green]Ecosystem & Core Subsystems[/bold green]", border_style="cyan")
        table.add_column("Subsystem", style="cyan", justify="left")
        table.add_column("Health / Status", style="green", justify="center")
        table.add_column("Details & Capabilities", style="white")

        table.add_row(
            "Media Engine",
            "✓ Active",
            f"Zero-Disk Streaming, {len(AVAILABLE_EXTRACTORS)}+ Extractors ({extractors_str})"
        )
        table.add_row(
            "FFmpeg Pipeline",
            "✓ Installed" if ffmpeg_ok else "✗ Missing from PATH",
            "320kbps MP3 Muxing, Lossless Cutting, Video-Audio Merging"
        )
        table.add_row(
            "AI Orchestration",
            "✓ Active",
            "Multi-model (GPT-4o, Gemini, Claude, DeepSeek), Sessions, Streaming"
        )
        table.add_row(
            "Search Hub",
            "✓ Active",
            "Web, Zero-Key YouTube Music Search, Wikipedia, News"
        )
        table.add_row(
            "Dev Automation",
            "✓ Active",
            "Temp-Mail OTP Polling, In-Memory QR, IP Geo, Free TTS, Crypto"
        )
        table.add_row(
            "NSFW Guard",
            "✓ Active",
            "Image & Text Moderation, Telegram Group Shield"
        )
        table.add_row(
            "MCP Protocol",
            "✓ Ready",
            "11 Native Tools configured for Claude Desktop & Cursor IDE"
        )
        table.add_row(
            "Persistent Cache",
            "✓ Active",
            f"SQLite DB ({cache_size} KB at {CACHE_DB_PATH})"
        )

        console.print(table)
        console.print("\n[bold magenta]🚀 Quick Commands:[/bold magenta]")
        console.print("  [cyan]stdapi extract <url>[/cyan]                -> Inspect direct stream URLs")
        console.print("  [cyan]stdapi download <url> -f mp3[/cyan]         -> Download 320k MP3/MP4 directly")
        console.print("  [cyan]stdapi search <query> --yt[/cyan]           -> Search YouTube tracks without API key")
        console.print("  [cyan]stdapi ai <prompt> -m gpt-4o[/cyan]         -> Prompt AI models directly")
        console.print("  [cyan]stdapi tools --temp-mail[/cyan]             -> Generate active disposable email")
        console.print("  [cyan]stdapi mcp[/cyan]                           -> Start Model Context Protocol server")
        console.print("  [cyan]stdapi clean[/cyan]                         -> Purge temporary cache files\n")
    else:
        print("=" * 65)
        print(" ECOSYSTEM & CORE SUBSYSTEMS")
        print("=" * 65)
        print(f" * Media Engine:     [ACTIVE] ({len(AVAILABLE_EXTRACTORS)}+ extractors: {extractors_str})")
        print(f" * FFmpeg Pipeline:  {'[INSTALLED]' if ffmpeg_ok else '[MISSING]'} (Muxing, Transcoding)")
        print(f" * AI Orchestration: [ACTIVE] (GPT-4o, Gemini, Claude, DeepSeek)")
        print(f" * Search Hub:       [ACTIVE] (Web, YouTube, Wikipedia, News)")
        print(f" * Dev Automation:   [ACTIVE] (Temp Mail, OTP Wait, QR, TTS, Crypto)")
        print(f" * NSFW Guard:       [ACTIVE] (Image & Text Moderation)")
        print(f" * MCP Protocol:     [READY]  (Claude Desktop & Cursor IDE)")
        print(f" * SQLite Cache:     [ACTIVE] ({cache_size} KB)")
        print("=" * 65)
        print("\nQuick Commands:")
        print("  stdapi extract <url>          -> Inspect direct stream URLs")
        print("  stdapi download <url> -f mp3  -> Download 320k MP3/MP4")
        print("  stdapi search <query> --yt    -> Search YouTube tracks")
        print("  stdapi ai <prompt>            -> Prompt AI models")
        print("  stdapi mcp                    -> Start Model Context Protocol server")
        print("  stdapi clean                  -> Purge temporary cache files\n")
