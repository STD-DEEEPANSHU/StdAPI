import pytest
from io import BytesIO
from stdapi.client import StdAPIClient
from stdapi.nsfw import NSFWModule


@pytest.mark.asyncio
async def test_nsfw_text_check():
    async with StdAPIClient() as client:
        nsfw = NSFWModule(client)
        clean = await nsfw.check_text("Welcome to our developer community!")
        assert clean.is_toxic is False

        flagged = await nsfw.check_text("watch this nsfw porn clip")
        assert flagged.is_toxic is True
        assert len(flagged.matches) > 0


@pytest.mark.asyncio
async def test_nsfw_is_safe_bytes():
    async with StdAPIClient() as client:
        nsfw = NSFWModule(client)
        fake_image = BytesIO(b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")
        safe = await nsfw.is_safe(fake_image)
        assert isinstance(safe, bool)
