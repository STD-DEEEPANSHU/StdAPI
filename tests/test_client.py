import pytest
from stdapi.client import StdAPIClient
from stdapi.exceptions import StdAPIError, RateLimitError, AuthenticationError


def test_client_init_and_properties():
    client = StdAPIClient(api_key="test_key", base_url="https://api.test.com")
    assert client.api_key == "test_key"
    assert client.base_url == "https://api.test.com"

    # Module accessors
    assert client.media is not None
    assert client.ai is not None
    assert client.search is not None
    assert client.tools is not None
    assert client.nsfw is not None
    assert client.agent is not None


def test_exceptions_hierarchy():
    assert issubclass(RateLimitError, StdAPIError)
    assert issubclass(AuthenticationError, StdAPIError)

    err = RateLimitError("Too many requests", retry_after=30)
    assert err.status_code == 429
    assert err.retry_after == 30
