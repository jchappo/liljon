"""Tests for the device token generator."""

import re

from liljon.auth._device_token import generate_device_token


def test_format():
    """Generated token should be hex with dashes: 8-4-4-4-12 groups."""
    token = generate_device_token()
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    assert re.match(pattern, token), f"Token {token!r} doesn't match expected 8-4-4-4-12 hex pattern"


def test_uniqueness():
    """Two generated tokens should be different."""
    t1 = generate_device_token()
    t2 = generate_device_token()
    assert t1 != t2
