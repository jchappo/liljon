"""Tests for the async HTTP transport."""

import pytest

from liljon._http import HttpTransport
from liljon.exceptions import APIError, NotAuthenticatedError, RateLimitError, SessionRevokedError


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


async def test_get_retries_on_502(transport, httpx_mock, monkeypatch):
    """Transient 502 → retry → eventual success returns parsed body."""
    monkeypatch.setattr("liljon._http._GET_RETRY_DELAYS", (0.0, 0.0, 0.0))
    httpx_mock.add_response(url="https://api.robinhood.com/test/", status_code=502, text="bad gateway")
    httpx_mock.add_response(url="https://api.robinhood.com/test/", status_code=502, text="bad gateway")
    httpx_mock.add_response(url="https://api.robinhood.com/test/", json={"ok": True})
    data = await transport.get("https://api.robinhood.com/test/")
    assert data == {"ok": True}


async def test_get_retries_on_503_and_504(transport, httpx_mock, monkeypatch):
    """503 and 504 are also retried."""
    monkeypatch.setattr("liljon._http._GET_RETRY_DELAYS", (0.0, 0.0, 0.0))
    httpx_mock.add_response(url="https://api.robinhood.com/test/", status_code=503, text="unavailable")
    httpx_mock.add_response(url="https://api.robinhood.com/test/", status_code=504, text="timeout")
    httpx_mock.add_response(url="https://api.robinhood.com/test/", json={"ok": True})
    data = await transport.get("https://api.robinhood.com/test/")
    assert data == {"ok": True}


async def test_get_retries_on_grpc_auth_leak(transport, httpx_mock, monkeypatch):
    """ceres gRPC 403 'Authorization key does not exist in metadata' is a flap."""
    monkeypatch.setattr("liljon._http._GET_RETRY_DELAYS", (0.0, 0.0, 0.0))
    httpx_mock.add_response(
        url="https://api.robinhood.com/ceres/v1/orders/",
        status_code=403,
        json={"code": 7, "message": 'the "Authorization" key does not exist in metadata', "details": []},
    )
    httpx_mock.add_response(
        url="https://api.robinhood.com/ceres/v1/orders/",
        json={"results": []},
    )
    data = await transport.get("https://api.robinhood.com/ceres/v1/orders/")
    assert data == {"results": []}


async def test_get_does_not_retry_on_real_403(transport, httpx_mock):
    """A normal 403 (not the gRPC auth-leak signature) should NOT be retried."""
    httpx_mock.add_response(
        url="https://api.robinhood.com/test/",
        status_code=403,
        json={"detail": "Permission denied"},
    )
    with pytest.raises(APIError) as exc_info:
        await transport.get("https://api.robinhood.com/test/")
    assert exc_info.value.status_code == 403


async def test_get_gives_up_after_max_retries(transport, httpx_mock, monkeypatch):
    """If transient errors persist past the retry budget, surface APIError."""
    monkeypatch.setattr("liljon._http._GET_RETRY_DELAYS", (0.0, 0.0, 0.0))
    for _ in range(4):  # 1 initial + 3 retries
        httpx_mock.add_response(url="https://api.robinhood.com/test/", status_code=502, text="bad gateway")
    with pytest.raises(APIError) as exc_info:
        await transport.get("https://api.robinhood.com/test/")
    assert exc_info.value.status_code == 502


async def test_post_does_not_retry_on_502(transport, httpx_mock):
    """POSTs are not retried — could double-submit orders."""
    httpx_mock.add_response(
        url="https://api.robinhood.com/orders/", status_code=502, text="bad gateway"
    )
    with pytest.raises(APIError) as exc_info:
        await transport.post("https://api.robinhood.com/orders/", json={"x": 1})
    assert exc_info.value.status_code == 502


async def test_token_revoked_recreates_client_and_recovers(transport, httpx_mock):
    """First 401 with rh-auth-blocked-reason:token_revoked → discard httpx client → retry succeeds.

    Mirrors the production failure mode where the running process gets stuck 401-ing while a
    fresh process (same cached token) recovers. Recreating the client in-place should be
    equivalent to a process restart from Robinhood's perspective.
    """
    transport.set_auth("Bearer", "token-still-valid")
    httpx_mock.add_response(
        url="https://api.robinhood.com/markets/XNYS/hours/2026-05-04/",
        status_code=401,
        text="Unauthorized",
        headers={"rh-auth-blocked-reason": "token_revoked"},
    )
    httpx_mock.add_response(
        url="https://api.robinhood.com/markets/XNYS/hours/2026-05-04/",
        json={"is_open": True},
    )
    data = await transport.get("https://api.robinhood.com/markets/XNYS/hours/2026-05-04/")
    assert data == {"is_open": True}


async def test_token_revoked_persists_raises_session_revoked(transport, httpx_mock):
    """When recreation does not clear the revocation, raise SessionRevokedError so callers know
    the session is genuinely dead and an interactive re-login is required.
    """
    transport.set_auth("Bearer", "token-actually-dead")
    for _ in range(2):
        httpx_mock.add_response(
            url="https://api.robinhood.com/test/",
            status_code=401,
            text="Unauthorized",
            headers={"rh-auth-blocked-reason": "token_revoked"},
        )
    with pytest.raises(SessionRevokedError):
        await transport.get("https://api.robinhood.com/test/")


async def test_401_without_token_revoked_header_no_retry(transport, httpx_mock):
    """A plain 401 (no token_revoked header) is not the stuck-state pattern — surface it directly
    so callers see NotAuthenticatedError on the first attempt without burning a recreation cycle.
    """
    httpx_mock.add_response(
        url="https://api.robinhood.com/test/",
        status_code=401,
        json={"detail": "Bad token"},
    )
    with pytest.raises(NotAuthenticatedError) as exc_info:
        await transport.get("https://api.robinhood.com/test/")
    assert not isinstance(exc_info.value, SessionRevokedError)


async def test_token_revoked_recreation_preserves_auth_header(transport, httpx_mock):
    """The recreated httpx client must carry the same Authorization header — recreation only
    discards connection state, not credentials.
    """
    transport.set_auth("Bearer", "preserved-token")
    httpx_mock.add_response(
        url="https://api.robinhood.com/test/",
        status_code=401,
        text="Unauthorized",
        headers={"rh-auth-blocked-reason": "token_revoked"},
    )
    httpx_mock.add_response(url="https://api.robinhood.com/test/", json={"ok": True})
    await transport.get("https://api.robinhood.com/test/")
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert requests[0].headers.get("Authorization") == "Bearer preserved-token"
    assert requests[1].headers.get("Authorization") == "Bearer preserved-token"


async def test_token_revoked_on_post_also_recovers(transport, httpx_mock):
    """The recreate-and-retry path applies to POST as well (e.g. /oauth2/token/ refresh calls)."""
    transport.set_auth("Bearer", "token-still-valid")
    httpx_mock.add_response(
        url="https://api.robinhood.com/oauth2/token/",
        status_code=401,
        text="Unauthorized",
        headers={"rh-auth-blocked-reason": "token_revoked"},
    )
    httpx_mock.add_response(
        url="https://api.robinhood.com/oauth2/token/",
        json={"access_token": "new", "expires_in": 86400},
    )
    data = await transport.post(
        "https://api.robinhood.com/oauth2/token/",
        data={"grant_type": "refresh_token"},
        raise_on_error=False,
    )
    assert data["access_token"] == "new"
