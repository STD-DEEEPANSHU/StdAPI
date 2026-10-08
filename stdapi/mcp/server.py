"""
StdAPI Model Context Protocol (MCP) Server
Allows Claude Desktop, Cursor IDE, Windsurf, and AI Agents to use StdAPI
as native functions to inspect media, search the web, generate temp mail,
run FFmpeg operations, and fetch geolocation.
"""
import sys
import json
import asyncio
from typing import Dict, Any

from ..extractors.registry import find_extractor
from ..core.ffmpeg import FFmpegPipeline
from ..client import StdAPIClient

_client = StdAPIClient()

TOOLS_MANIFEST = [
    {
        "name": "extract_media",
        "description": "Extract direct stream URL, title, thumbnail, and author from YouTube, Instagram, TikTok, Twitter/X, or Pinterest.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The media URL to inspect and extract"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "convert_media",
        "description": "Convert video or audio file to 320kbps MP3 or trim it using in-process FFmpeg.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_file": {"type": "string", "description": "Path to input file"},
                "output_file": {"type": "string", "description": "Path for output MP3"},
                "bitrate": {"type": "string", "default": "320k"}
            },
            "required": ["input_file", "output_file"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for up-to-date information, snippets, and source links.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Web search query"},
                "limit": {"type": "integer", "default": 5, "description": "Number of results to return"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_youtube",
        "description": "Search YouTube for music, tracks, and videos without an API key (returns titles, URLs, thumbnails, durations).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Song name or video topic to search"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_wiki",
        "description": "Look up comprehensive summary and references from Wikipedia.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic or entity to look up"},
                "lang": {"type": "string", "default": "en"}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "ai_chat",
        "description": "Prompt advanced AI models (GPT-4o, Claude 3.5, Gemini, DeepSeek).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The prompt or instruction for the AI"},
                "model": {"type": "string", "default": "gpt-4o-mini", "description": "Model identifier"}
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "temp_mail_create",
        "description": "Create an active disposable email address for testing or signups.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "temp_mail_inbox",
        "description": "Check the inbox of a disposable email for incoming emails and verification OTPs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "login": {"type": "string", "description": "Username part before @"},
                "domain": {"type": "string", "description": "Domain part after @"}
            },
            "required": ["login", "domain"]
        }
    },
    {
        "name": "ip_lookup",
        "description": "Lookup geolocation, city, country, and ISP details for any IP address or 'me'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ip": {"type": "string", "description": "IP address to inspect, or leave empty for current server IP"}
            }
        }
    },
    {
        "name": "generate_qr_code",
        "description": "Generate a QR code image data URL for any text or link.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text or URL to encode in QR code"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "scan_nsfw",
        "description": "Scan an image URL or image file for NSFW / 18+ content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Image URL to scan"},
                "threshold": {"type": "number", "default": 0.65}
            },
            "required": ["url"]
        }
    }
]


async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if name == "extract_media":
            url = arguments.get("url", "")
            extractor = find_extractor(url)
            if not extractor:
                return {"error": f"No supported extractor for URL: {url}"}
            res = await extractor.extract(url)
            return res.to_dict()

        elif name == "convert_media":
            in_f = arguments["input_file"]
            out_f = arguments["output_file"]
            bitrate = arguments.get("bitrate", "320k")
            success = await FFmpegPipeline.convert_to_audio(in_f, out_f, bitrate)
            return {"success": success, "output": out_f}

        elif name == "search_web":
            res = await _client.search.web(arguments.get("query", ""), limit=arguments.get("limit", 5))
            return res.to_dict()

        elif name == "search_youtube":
            res = await _client.search.youtube(arguments.get("query", ""), limit=arguments.get("limit", 5))
            return res.to_dict()

        elif name == "search_wiki":
            res = await _client.search.wiki(arguments.get("topic", ""), lang=arguments.get("lang", "en"))
            return res.to_dict()

        elif name == "ai_chat":
            res = await _client.ai.chat(arguments.get("prompt", ""), model=arguments.get("model", "gpt-4o-mini"))
            return res.to_dict()

        elif name == "temp_mail_create":
            res = await _client.tools.temp_mail()
            return res.to_dict()

        elif name == "temp_mail_inbox":
            res = await _client.tools.temp_mail_inbox(arguments.get("login", ""), arguments.get("domain", ""))
            return res.to_dict()

        elif name == "ip_lookup":
            res = await _client.tools.ip(arguments.get("ip"))
            return res.to_dict()

        elif name == "generate_qr_code":
            res = await _client.tools.qr(arguments.get("text", ""))
            return res.to_dict()

        elif name == "scan_nsfw":
            res = await _client.nsfw.check(arguments.get("url", ""), threshold=arguments.get("threshold", 0.65))
            return res.to_dict()

        return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"error": str(e)}


async def run_stdio_mcp_server():
    """Run JSON-RPC 2.0 stdio loop for Claude / Cursor / Zed MCP integrations."""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break
        try:
            req = json.loads(line.decode().strip())
            req_id = req.get("id")
            method = req.get("method")

            if method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS_MANIFEST}}
            elif method == "tools/call":
                params = req.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})
                result = await handle_tool_call(name, args)
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()
