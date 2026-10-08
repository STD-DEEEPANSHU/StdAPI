import pytest
from stdapi.client import StdAPIClient
from stdapi.ai import AIModule, AISession


@pytest.mark.asyncio
async def test_ai_session_history():
    async with StdAPIClient() as client:
        ai = AIModule(client)
        session = ai.create_session(system_prompt="Test system")
        assert len(session.history) == 1
        assert session.history[0]["content"] == "Test system"

        res = await session.ask("Hello")
        assert res.success is True
        assert len(session.history) == 3

        session.clear()
        assert len(session.history) == 1
