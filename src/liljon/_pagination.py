"""Pagination helpers for Robinhood API responses.

Two strategies:
1. URL-based: standard `next` URL in response body (stocks, options, account)
2. Cursor-based: `cursor` field in response body (futures)
"""

from __future__ import annotations

import logging
from typing import Any

from liljon._http import HttpTransport

logger = logging.getLogger(__name__)


async def paginate_results(
    transport: HttpTransport,
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """Collect all results from a URL-paginated endpoint.

    Follows the `next` URL in each response until exhausted or max_pages reached.
    """
    all_results: list[dict[str, Any]] = []
    current_url: str | None = url
    page = 0

    while current_url and page < max_pages:
        data = await transport.get(current_url, params=params if page == 0 else None, headers=headers)

        results = data.get("results", [])
        all_results.extend(r for r in results if r is not None)

        current_url = data.get("next")
        page += 1

    return all_results


async def paginate_cursor(
    transport: HttpTransport,
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """Collect all results from a cursor-paginated endpoint (futures).

    Uses the `cursor` field from the response to fetch subsequent pages.
    """
    all_results: list[dict[str, Any]] = []
    current_params = dict(params) if params else {}
    page = 0

    while page < max_pages:
        data = await transport.get(url, params=current_params, headers=headers)

        results = data.get("results", [])
        all_results.extend(r for r in results if r is not None)

        cursor = data.get("cursor")
        if not cursor:
            break

        current_params["cursor"] = cursor
        page += 1

    return all_results
