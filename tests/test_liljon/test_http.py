"""Tests for the async HTTP transport."""

import pytest
import httpx

from liljon._http import HttpTransport
from liljon.exceptions import APIError, NotAuthenticatedError, RateLimitError


@pytest.fixture
def transport():
    return HttpTransport(timeout=5.0)


def test_set_and_clear_auth(transport):
    assert not transport.is_authenticated
    transport.set_auth("Bearer", "abc123")
    assert transport.is_authenticated
    transport.clear_auth()
    assert not transport.is_authenticated


async def test_get_success(transport, httpx_mock):
    httpx_mock.add_response(url="https://api.robinhood.com/test/", json={"ok": True})
    data = await transport.get("https://api.robinhood.com/test/")
    assert data == {"ok": True}


async def test_get_with_params(transport, httpx_mock):
    httpx_mock.add_response(url="https://api.robinhood.com/test/?foo=bar", json={"ok": True})
    data = await transport.get("https://api.robinhood.com/test/", params={"foo": "bar"})
    assert data == {"ok": True}


async def test_post_success(transport, httpx_mock):
    httpx_mock.add_response(url="https://api.robinhood.com/test/", json={"id": "123"})
    data = await transport.post("https://api.robinhood.com/test/", json={"key": "value"})
    assert data["id"] == "123"


async def test_401_raises_not_authenticated(transport, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/test/",
        status_code=401,
        json={"detail": "Not authenticated"},
    )
    with pytest.raises(NotAuthenticatedError, match="Authentication required"):
        await transport.get("https://api.robinhood.com/test/")


async def test_429_raises_rate_limit(transport, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/test/",
        status_code=429,
        json={"detail": "Too many requests"},
        headers={"Retry-After": "30"},
    )
    with pytest.raises(RateLimitError) as exc_info:
        await transport.get("https://api.robinhood.com/test/")
    assert exc_info.value.retry_after == 30.0


async def test_500_raises_api_error(transport, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/test/",
        status_code=500,
        json={"detail": "Internal server error"},
    )
    with pytest.raises(APIError) as exc_info:
        await transport.get("https://api.robinhood.com/test/")
    assert exc_info.value.status_code == 500


async def test_delete_204(transport, httpx_mock):
    httpx_mock.add_response(url="https://api.robinhood.com/test/", status_code=204)
    result = await transport.delete("https://api.robinhood.com/test/")
    assert result is None


async def test_close(transport):
    await transport.close()  # Should not raise
