"""Generate a Robinhood-compatible device token.

Ported from robin_stocks.robinhood.authentication.generate_device_token().
The token is a hex string with dashes, matching the format Robinhood expects.
"""

from __future__ import annotations

import secrets


def generate_device_token() -> str:
    """Generate a random device token for Robinhood authentication.

    Matches robin_stocks' algorithm: 16 random bytes → 32 hex chars with
    dashes inserted after positions 8, 12, 16, and 20.
    """
    rands = [secrets.randbelow(256) for _ in range(16)]
    hexa = [format(i + 256, "x")[1:] for i in range(256)]
    token = ""
    for i, r in enumerate(rands):
        token += hexa[r]
        if i in (3, 5, 7, 9):
            token += "-"
    return token
