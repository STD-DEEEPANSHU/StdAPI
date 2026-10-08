import pytest
import asyncio
from stdapi.tools import ToolsModule
from stdapi.client import StdAPIClient


def test_tools_hash():
    res = ToolsModule.hash("hello world", algo="sha256")
    assert res.algorithm == "sha256"
    assert res.digest == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_tools_password():
    pwd = ToolsModule.password(length=20)
    assert len(pwd) == 20
    assert isinstance(pwd, str)


def test_tools_uuid():
    u = ToolsModule.uuid()
    assert len(u) == 36
    assert "-" in u


@pytest.mark.asyncio
async def test_tools_qr_local():
    async with StdAPIClient() as client:
        tools = ToolsModule(client)
        res = await tools.qr("https://github.com/STD-DEEPANSHU")
        assert res.success is True
        assert res.text == "https://github.com/STD-DEEPANSHU"
