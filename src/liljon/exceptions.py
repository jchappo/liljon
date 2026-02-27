"""Custom exception hierarchy for the Robinhood client.

All exceptions inherit from RobinhoodError so callers can catch
the entire family with a single except clause.
"""

from __future__ import annotations


class RobinhoodError(Exception):
    """Base exception for all Robinhood client errors."""


class AuthenticationError(RobinhoodError):
    """Raised when login, 2FA, or token refresh fails."""


class NotAuthenticatedError(AuthenticationError):
    """Raised when an API call is made without a valid session (HTTP 401)."""


class ChallengeRequiredError(AuthenticationError):
    """Raised when Robinhood requires additional verification to proceed."""

    def __init__(self, challenge_type: str, challenge_id: str, machine_id: str, msg: str = "") -> None:
        self.challenge_type = challenge_type
        self.challenge_id = challenge_id
        self.machine_id = machine_id
        super().__init__(msg or f"Verification required via {challenge_type}")


class APIError(RobinhoodError):
    """Raised for non-2xx HTTP responses from the Robinhood API."""

    def __init__(self, status_code: int, url: str, detail: str = "") -> None:
        self.status_code = status_code
        self.url = url
        self.detail = detail
        super().__init__(f"HTTP {status_code} from {url}: {detail}" if detail else f"HTTP {status_code} from {url}")


class RateLimitError(APIError):
    """Raised when Robinhood returns HTTP 429 (Too Many Requests)."""

    def __init__(self, url: str, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        detail = f"retry after {retry_after}s" if retry_after else ""
        super().__init__(429, url, detail)


class InvalidSymbolError(RobinhoodError):
    """Raised when a ticker symbol cannot be resolved."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        super().__init__(f"Invalid or unrecognized symbol: {symbol}")


class OrderError(RobinhoodError):
    """Raised when an order placement or cancellation fails."""

    def __init__(self, detail: str, order_data: dict | None = None) -> None:
        self.order_data = order_data or {}
        super().__init__(detail)


class ValidationError(RobinhoodError):
    """Raised for client-side validation failures (bad parameters, missing fields)."""
