import pytest
from stdapi.mcp.server import TOOLS_MANIFEST, handle_tool_call


def test_mcp_manifest():
    assert len(TOOLS_MANIFEST) >= 10
    names = [t["name"] for t in TOOLS_MANIFEST]
    assert "extract_media" in names
    assert "search_web" in names
    assert "search_youtube" in names
    assert "temp_mail_create" in names
    assert "ip_lookup" in names


@pytest.mark.asyncio
async def test_mcp_tool_call():
    res = await handle_tool_call("generate_qr_code", {"text": "hello mcp"})
    assert "data_url" in res or "qr_image_url" in res

    unknown = await handle_tool_call("nonexistent_tool", {})
    assert "error" in unknown
