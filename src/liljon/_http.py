"""Async HTTP transport wrapping httpx with Robinhood-specific headers and error mapping.

Supports safe use across multiple event loops (e.g. FastAPI loop + background bridge loop)
by lazily creating an httpx.AsyncClient per event loop and tracking auth state separately.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from liljon.exceptions import APIError, NotAuthenticatedError, RateLimitError

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=1",
    "X-Robinhood-API-Version": "1.431.4",
    "Connection": "keep-alive",
    "User-Agent": "*",
}


class HttpTransport:
    """Async HTTP transport for all Robinhood API calls.

    Wraps httpx.AsyncClient with pre-configured headers, auth management,
    and error-to-exception mapping.  The underlying client is created lazily
    and re-created when the running event loop changes, preventing
    "bound to a different event loop" errors when a singleton
    RobinhoodClient is shared between FastAPI routes and a background
    async-bridge loop.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._headers: dict[str, str] = _DEFAULT_HEADERS.copy()
        self._client: httpx.AsyncClient | None = None
        self._bound_loop_id: int | None = None

    def _ensure_client(self) -> httpx.AsyncClient:
        """Return an httpx client bound to the current event loop.

        If the event loop has changed since the last client was created,
        the old client is discarded and a fresh one is created so that
        internal asyncio primitives (locks, events) belong to the
        correct loop.
        """
        try:
            loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            loop_id = None

        if self._client is not None and self._bound_loop_id == loop_id:
            return self._client

        # Event loop changed or first use — create a fresh client
        logger.debug("Creating new httpx.AsyncClient for event loop %s", loop_id)
        self._client = httpx.AsyncClient(
            headers=self._headers.copy(),
            timeout=httpx.Timeout(self._timeout),
            follow_redirects=True,
        )
        self._bound_loop_id = loop_id
        return self._client

    def set_auth(self, token_type: str, access_token: str) -> None:
        """Set the Authorization header for subsequent requests."""
        self._headers["Authorization"] = f"{token_type} {access_token}"
        if self._client is not None:
            self._client.headers["Authorization"] = f"{token_type} {access_token}"

    def clear_auth(self) -> None:
        """Remove the Authorization header."""
        self._headers.pop("Authorization", None)
        if self._client is not None:
            self._client.headers.pop("Authorization", None)

    @property
    def is_authenticated(self) -> bool:
        return "Authorization" in self._headers

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return the parsed JSON response."""
        resp = await self._ensure_client().get(url, params=params, headers=headers)
        self._raise_for_status(resp)
        return resp.json()

    async def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        raise_on_error: bool = True,
    ) -> dict[str, Any]:
        """Send a POST request and return the parsed JSON response.

        When raise_on_error is False, the JSON body is returned even for non-2xx
        responses (matching robin_stocks behavior for auth endpoints).
        """
        resp = await self._ensure_client().post(url, json=json, data=data, params=params, headers=headers)
        if raise_on_error:
            self._raise_for_status(resp)
        return resp.json()

    async def patch(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a PATCH request and return the parsed JSON response."""
        resp = await self._ensure_client().patch(url, json=json, params=params, headers=headers)
        self._raise_for_status(resp)
        return resp.json()

    async def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """Send a DELETE request. Returns parsed JSON or None for 204."""
        resp = await self._ensure_client().delete(url, headers=headers)
        self._raise_for_status(resp)
        if resp.status_code == 204:
            return None
        return resp.json()

    async def close(self) -> None:
        """Close the underlying httpx client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._bound_loop_id = None

    def _raise_for_status(self, resp: httpx.Response) -> None:
        """Map HTTP error status codes to typed exceptions."""
        if resp.is_success:
            return

        url = str(resp.url)
        status = resp.status_code

        # Extract detail from JSON body if possible
        detail = ""
        try:
            body = resp.json()
            logger.debug("Error response body: %s", body)
            detail = body.get("detail", body.get("error", body.get("non_field_errors", "")))
            if isinstance(detail, list):
                detail = "; ".join(str(d) for d in detail)
            if not detail:
                detail = str(body)
        except Exception:
            detail = resp.text[:500] if resp.text else ""

        if status == 401:
            raise NotAuthenticatedError(f"Authentication required for {url}: {detail}")
        if status == 429:
            retry_after = resp.headers.get("Retry-After")
            raise RateLimitError(url, float(retry_after) if retry_after else None)

        raise APIError(status, url, str(detail))
