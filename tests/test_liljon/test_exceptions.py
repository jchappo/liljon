"""Tests for the exception hierarchy."""

from liljon.exceptions import (
    APIError,
    AuthenticationError,
    ChallengeRequiredError,
    InvalidSymbolError,
    NotAuthenticatedError,
    OrderError,
    RateLimitError,
    RobinhoodError,
    ValidationError,
)


def test_hierarchy():
    """All exceptions inherit from RobinhoodError."""
    assert issubclass(AuthenticationError, RobinhoodError)
    assert issubclass(NotAuthenticatedError, AuthenticationError)
    assert issubclass(ChallengeRequiredError, AuthenticationError)
    assert issubclass(APIError, RobinhoodError)
    assert issubclass(RateLimitError, APIError)
    assert issubclass(InvalidSymbolError, RobinhoodError)
    assert issubclass(OrderError, RobinhoodError)
    assert issubclass(ValidationError, RobinhoodError)


def test_api_error_attributes():
    err = APIError(404, "https://api.robinhood.com/foo/", "not found")
    assert err.status_code == 404
    assert err.url == "https://api.robinhood.com/foo/"
    assert err.detail == "not found"
    assert "404" in str(err)
    assert "not found" in str(err)


def test_rate_limit_error():
    err = RateLimitError("https://api.robinhood.com/bar/", retry_after=60.0)
    assert err.status_code == 429
    assert err.retry_after == 60.0


def test_challenge_required_error():
    err = ChallengeRequiredError("sms", "abc123", "machine456")
    assert err.challenge_type == "sms"
    assert err.challenge_id == "abc123"
    assert err.machine_id == "machine456"
    assert "sms" in str(err)


def test_invalid_symbol_error():
    err = InvalidSymbolError("FAKESYMBOL")
    assert err.symbol == "FAKESYMBOL"
    assert "FAKESYMBOL" in str(err)


def test_order_error():
    err = OrderError("Insufficient funds", {"id": "123"})
    assert err.order_data == {"id": "123"}
    assert "Insufficient funds" in str(err)
