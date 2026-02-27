"""Pydantic models for the authentication flow."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TokenData(BaseModel):
    """Stored token data from a successful login."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    scope: str = "internal"
    device_token: str | None = None
    username: str | None = None
    account_number: str | None = None


class ChallengeInfo(BaseModel):
    """Details about a pending verification challenge."""

    challenge_id: str
    challenge_type: str  # "sms", "email", "prompt"
    machine_id: str
    status: str = "issued"


class LoginResult(BaseModel):
    """Result of a login or verification attempt."""

    status: Literal["logged_in", "challenge_required", "invalid_code", "expired", "error"]
    message: str
    username: str | None = None
    challenge: ChallengeInfo | None = None
