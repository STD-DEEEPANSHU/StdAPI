"""
StdAPI Unified Command Line Interface (CLI)
Universal developer toolkit for media downloading, AI chat, web search,
system utilities, NSFW detection, and autonomous agent orchestration.
"""
import sys
import os
import json
import asyncio
import argparse
from pathlib import Path

from ..client import StdAPIClient
from ..extractors.registry import find_extractor
from ..core.ffmpeg import FFmpegPipeline
from ..mcp.server import run_stdio_mcp_server
from .tui import show_diagnostics

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


def safe_print(text: str):
    if HAS_RICH and console:
        console.print(text)
    else:
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", "replace").decode("ascii"))


def print_json(data):
    safe_print(json.dumps(data, indent=2, default=str))


def main():
    common_parent = argparse.ArgumentParser(add_help=False)
    common_parent.add_argument("--json", action="store_true", help="Output results in JSON format")

    parser = argparse.ArgumentParser(
        prog="stdapi",
        description="StdAPI 2.3.0 — Unified API Platform for AI, Media, Search & Automation.",
        parents=[common_parent]
    )
    parser.add_argument("-v", "--version", action="version", version="StdAPI 2.3.0")

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # 1. extract command
    p_extract = subparsers.add_parser("extract", parents=[common_parent], help="Inspect and extract direct stream URL")
    p_extract.add_argument("url", help="Media URL (YouTube, Instagram, TikTok, Twitter/X, Pinterest)")

    # 2. download command
    p_download = subparsers.add_parser("download", parents=[common_parent], help="Download video or audio stream")
    p_download.add_argument("url", help="Media URL")
    p_download.add_argument("-f", "--format", default="mp4", choices=["mp4", "mp3", "m4a"], help="Format (default: mp4)")
    p_download.add_argument("-o", "--output", help="Save file path")

    # 3. ai command
    p_ai = subparsers.add_parser("ai", parents=[common_parent], help="Ask AI models questions or generate code")
    p_ai.add_argument("prompt", help="Prompt for AI")
    p_ai.add_argument("-m", "--model", default="gpt-4o-mini", help="Model (gpt-4o-mini, gemini, deepseek, claude)")
    p_ai.add_argument("-s", "--system", help="Optional system prompt")

    # 4. search command
    p_search = subparsers.add_parser("search", parents=[common_parent], help="Search the web, YouTube, or Wikipedia")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--yt", "--youtube", dest="youtube", action="store_true", help="Search YouTube specifically")
    p_search.add_argument("--wiki", action="store_true", help="Search Wikipedia specifically")
    p_search.add_argument("--news", action="store_true", help="Search news headlines")
    p_search.add_argument("-l", "--limit", type=int, default=5, help="Number of results")

    # 5. tools command
    p_tools = subparsers.add_parser("tools", parents=[common_parent], help="Developer utilities")
    p_tools.add_argument("--temp-mail", action="store_true", help="Generate active disposable email")
    p_tools.add_argument("--ip", nargs="?", const="me", help="Lookup IP geolocation")
    p_tools.add_argument("--qr", help="Generate QR code for text")
    p_tools.add_argument("--shorten", help="Shorten long URL")
    p_tools.add_argument("--crypto", nargs="?", const="BTC", help="Get crypto price ticker")
    p_tools.add_argument("--currency", nargs=3, metavar=("AMOUNT", "FROM", "TO"), help="Convert currency e.g. 100 USD INR")
    p_tools.add_argument("--tts", help="Generate text to speech voice file")
    p_tools.add_argument("--hash", nargs=2, metavar=("TEXT", "ALGO"), help="Hash string e.g. 'hello' sha256")
    p_tools.add_argument("--password", type=int, nargs="?", const=16, help="Generate strong password")

    # 6. nsfw command
    p_nsfw = subparsers.add_parser("nsfw", parents=[common_parent], help="Scan image or text for NSFW content")
    p_nsfw.add_argument("target", help="Image URL, image file path, or text")
    p_nsfw.add_argument("-t", "--threshold", type=float, default=0.65, help="Detection threshold")

    # 7. convert command
    p_convert = subparsers.add_parser("convert", parents=[common_parent], help="Convert media to 320kbps MP3")
    p_convert.add_argument("input", help="Input file path")
    p_convert.add_argument("output", help="Output file path")
    p_convert.add_argument("-b", "--bitrate", default="320k", help="Audio bitrate")

    # 8. agent command
    p_agent = subparsers.add_parser("agent", parents=[common_parent], help="Execute autonomous agent task on desktop")
    p_agent.add_argument("mission", help="Task description")

    # 9. hud command
    subparsers.add_parser("hud", help="Launch native Virtual Desktop HUD window")

    # 10. clean command
    subparsers.add_parser("clean", help="Scan and clean temporary OS cache")

    # 11. mcp command
    subparsers.add_parser("mcp", help="Start Model Context Protocol (MCP) server")

    # 12. tui command
    subparsers.add_parser("tui", help="Show interactive diagnostics dashboard")

    args = parser.parse_args()

    if not args.command:
        show_diagnostics()
        sys.exit(0)

    if args.command == "tui":
        show_diagnostics()
        sys.exit(0)

    if args.command == "mcp":
        asyncio.run(run_stdio_mcp_server())
        return

    # Runner for async commands
    async def run_async():
        async with StdAPIClient() as api:
            if args.command == "extract":
                extractor = find_extractor(args.url)
                if not extractor:
                    print(f"[-] Unsupported URL: {args.url}")
                    return
                res = await extractor.extract(args.url)
                if args.json:
                    print_json(res.to_dict())
                elif HAS_RICH:
                    table = Table(title=f"[bold green]✓ Extracted: {res.extractor}[/bold green]", border_style="green")
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="white")
                    table.add_row("Title", res.title)
                    table.add_row("Author", res.author or "Unknown")
                    table.add_row("Duration", f"{res.duration}s" if res.duration else "N/A")
                    table.add_row("Direct Stream", res.best_video_url or "N/A")
                    console.print(table)
                else:
                    print(f"\n✓ Extracted: {res.extractor}")
                    print(f"  Title:         {res.title}")
                    print(f"  Author:        {res.author or 'Unknown'}")
                    print(f"  Duration:      {res.duration or 'N/A'}")
                    print(f"  Direct Stream: {res.best_video_url or 'N/A'}\n")

            elif args.command == "download":
                out_file = args.output or f"download.{args.format}"
                if HAS_RICH and not args.json:
                    console.print(f"[*] Extracting and downloading stream from: [cyan]{args.url}[/cyan]...")

                buf = await api.media.get_buffer(args.url, format=args.format)
                with open(out_file, "wb") as f:
                    f.write(buf.getvalue())

                if args.json:
                    print_json({"success": True, "saved_to": out_file, "bytes": len(buf.getvalue())})
                elif HAS_RICH:
                    console.print(f"[bold green]✓ Downloaded successfully:[/bold green] [white]{out_file}[/white] ({round(len(buf.getvalue())/1024/1024, 2)} MB)")
                else:
                    print(f"✓ Downloaded successfully: {out_file} ({round(len(buf.getvalue())/1024/1024, 2)} MB)")

            elif args.command == "ai":
                res = await api.ai.chat(args.prompt, model=args.model, system_prompt=args.system)
                if args.json:
                    print_json(res.to_dict())
                elif HAS_RICH:
                    console.print(Panel(res.get("response", ""), title=f"[bold magenta]StdAI ({args.model})[/bold magenta]", border_style="magenta"))
                else:
                    print(f"\n[AI ({args.model})]:\n{res.get('response', '')}\n")

            elif args.command == "search":
                if args.youtube:
                    res = await api.search.youtube(args.query, limit=args.limit)
                    if args.json:
                        print_json(res.to_dict())
                    elif HAS_RICH:
                        table = Table(title=f"YouTube Results for '{args.query}'", border_style="red")
                        table.add_column("#", style="cyan")
                        table.add_column("Title", style="white")
                        table.add_column("Channel", style="yellow")
                        table.add_column("URL", style="blue")
                        for i, r in enumerate(res.get("results", []), 1):
                            table.add_row(str(i), r.get("title", ""), r.get("channel", ""), r.get("url", ""))
                        console.print(table)
                    else:
                        print(f"\nYouTube Results for '{args.query}':")
                        for i, r in enumerate(res.get("results", []), 1):
                            print(f"{i}. {r.get('title')} ({r.get('channel')})\n   {r.get('url')}\n")

                elif args.wiki:
                    res = await api.search.wiki(args.query)
                    if args.json:
                        print_json(res.to_dict())
                    elif HAS_RICH:
                        console.print(Panel(res.get("extract", ""), title=f"[bold blue]Wikipedia: {res.get('title')}[/bold blue]"))
                    else:
                        print(f"\n[Wikipedia: {res.get('title')}]\n{res.get('extract')}\n")

                else:
                    res = await api.search.web(args.query, limit=args.limit)
                    if args.json:
                        print_json(res.to_dict())
                    elif HAS_RICH:
                        table = Table(title=f"Web Results for '{args.query}'", border_style="cyan")
                        table.add_column("#", style="cyan")
                        table.add_column("Title", style="white")
                        table.add_column("Snippet", style="dim")
                        table.add_column("URL", style="blue")
                        for i, r in enumerate(res.get("results", []), 1):
                            table.add_row(str(i), r.get("title", ""), r.get("snippet", "")[:100], r.get("url", ""))
                        console.print(table)
                    else:
                        print(f"\nResults for '{args.query}':")
                        for i, r in enumerate(res.get("results", []), 1):
                            print(f"{i}. {r.get('title')}\n   {r.get('url')}\n   {r.get('snippet')}\n")

            elif args.command == "tools":
                if args.temp_mail:
                    res = await api.tools.temp_mail()
                    if args.json:
                        print_json(res.to_dict())
                    else:
                        safe_print(f"[+] Active Temp Mail: {res.get('email')}")
                        safe_print(f"    Login: {res.get('login')} | Domain: {res.get('domain')}")

                elif args.ip:
                    ip_arg = None if args.ip == "me" else args.ip
                    res = await api.tools.ip(ip_arg)
                    if args.json:
                        print_json(res.to_dict())
                    else:
                        safe_print(f"[+] IP: {res.get('ip')}")
                        safe_print(f"    Location: {res.get('city')}, {res.get('region')}, {res.get('country')}")
                        safe_print(f"    ISP: {res.get('org')}")

                elif args.qr:
                    res = await api.tools.qr(args.qr)
                    if args.json:
                        print_json(res.to_dict())
                    else:
                        safe_print(f"[+] QR Link: {res.get('qr_image_url')}")

                elif args.shorten:
                    res = await api.tools.shorten(args.shorten)
                    if args.json:
                        print_json(res.to_dict())
                    else:
                        safe_print(f"[+] Shortened URL: {res.get('short_url')}")

                elif args.crypto:
                    res = await api.tools.crypto(args.crypto)
                    if args.json:
                        print_json(res.to_dict())
                    else:
                        safe_print(f"[+] {res.get('symbol')}: ${res.get('price_usd')} (24h Change: {res.get('change_24h_percent')}%)")

                elif args.currency:
                    amt, f_curr, t_curr = float(args.currency[0]), args.currency[1], args.currency[2]
                    res = await api.tools.currency(amount=amt, from_curr=f_curr, to_curr=t_curr)
                    if args.json:
                        print_json(res.to_dict())
                    else:
                        safe_print(f"[+] {amt} {f_curr.upper()} = {res.get('converted_amount')} {t_curr.upper()} (Rate: {res.get('rate')})")

                elif args.tts:
                    buf = await api.tools.tts(args.tts)
                    out_f = "tts.mp3"
                    with open(out_f, "wb") as f:
                        f.write(buf.getvalue())
                    safe_print(f"[+] Audio saved to {out_f}")

                elif args.hash:
                    res = api.tools.hash(args.hash[0], algo=args.hash[1])
                    if args.json:
                        print_json(res.to_dict())
                    else:
                        safe_print(f"[+] {args.hash[1].upper()} Digest: {res.get('digest')}")

                elif args.password:
                    pwd = api.tools.password(length=args.password)
                    if args.json:
                        print_json({"password": pwd, "length": len(pwd)})
                    else:
                        safe_print(f"[+] Generated Password: {pwd}")

            elif args.command == "nsfw":
                res = await api.nsfw.scan(args.target, threshold=args.threshold)
                if args.json:
                    print_json(res.to_dict())
                else:
                    status = "NSFW / EXPLICIT" if res.get("is_nsfw") else "SAFE"
                    safe_print(f"[{status}] Score: {res.get('score', 0.0)} | Threshold: {args.threshold}")

            elif args.command == "convert":
                success = await FFmpegPipeline.convert_to_audio(args.input, args.output, bitrate=args.bitrate)
                safe_print(f"[+] Converted to {args.output}" if success else "[!] Conversion failed.")

            elif args.command == "agent":
                from ..agent import StdAgent
                agent = StdAgent()
                agent.run(args.mission)

            elif args.command == "hud":
                from ..agent import StdAgent
                agent = StdAgent()
                agent.launch_hud()

            elif args.command == "clean":
                import shutil
                temp_dir = Path(os.environ.get("TEMP", Path.home() / "AppData/Local/Temp"))
                cleaned_mb = 0
                if temp_dir.exists():
                    for item in temp_dir.iterdir():
                        try:
                            if item.is_file() or item.is_symlink():
                                sz = item.stat().st_size
                                item.unlink(missing_ok=True)
                                cleaned_mb += sz / (1024 * 1024)
                            elif item.is_dir():
                                shutil.rmtree(item, ignore_errors=True)
                        except Exception:
                            pass
                print(f"[+] System Junk Cleared: {round(cleaned_mb, 1)} MB temporary cache freed.")

    asyncio.run(run_async())


if __name__ == "__main__":
    main()
