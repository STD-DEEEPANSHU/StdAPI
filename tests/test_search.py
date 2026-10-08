import pytest
from stdapi.client import StdAPIClient
from stdapi.search import SearchModule


@pytest.mark.asyncio
async def test_search_wiki_format():
    async with StdAPIClient() as client:
        search = SearchModule(client)
        res = await search.wiki("Python (programming language)")
        assert res.title is not None
        assert "Python" in res.title
