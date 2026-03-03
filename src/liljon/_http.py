"""Async HTTP transport wrapping httpx with Robinhood-specific headers and error mapping."""

from __future__ import annotations

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
    and error-to-exception mapping.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            headers=_DEFAULT_HEADERS.copy(),
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    def set_auth(self, token_type: str, access_token: str) -> None:
        """Set the Authorization header for subsequent requests."""
        self._client.headers["Authorization"] = f"{token_type} {access_token}"

    def clear_auth(self) -> None:
        """Remove the Authorization header."""
        self._client.headers.pop("Authorization", None)

    @property
    def is_authenticated(self) -> bool:
        return "Authorization" in self._client.headers

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return the parsed JSON response."""
        resp = await self._client.get(url, params=params, headers=headers)
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
        resp = await self._client.post(url, json=json, data=data, params=params, headers=headers)
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
        resp = await self._client.patch(url, json=json, params=params, headers=headers)
        self._raise_for_status(resp)
        return resp.json()

    async def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """Send a DELETE request. Returns parsed JSON or None for 204."""
        resp = await self._client.delete(url, headers=headers)
        self._raise_for_status(resp)
        if resp.status_code == 204:
            return None
        return resp.json()

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()

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
