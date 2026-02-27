"""Shared mixins and generic response wrappers."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class TimestampMixin(BaseModel):
    """Adds optional created/updated timestamps."""

    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Wrapper for paginated API results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    results: list[T]
    next_url: str | None = None
    previous_url: str | None = None
    count: int | None = None
