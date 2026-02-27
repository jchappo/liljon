"""Tests for the RobinhoodClient composition."""

import tempfile
from pathlib import Path

import pytest

from liljon.client import RobinhoodClient


async def test_client_creates_namespaces():
    async with RobinhoodClient() as client:
        assert client.stocks is not None
        assert client.options is not None
        assert client.crypto is not None
        assert client.futures is not None
        assert client.indexes is not None
        assert client.account is not None
        assert client.orders is not None
        assert client.markets is not None
        assert client.screeners is not None


async def test_client_not_authenticated_by_default():
    async with RobinhoodClient() as client:
        assert not client.is_authenticated


async def test_client_context_manager():
    client = RobinhoodClient()
    async with client:
        assert client.stocks is not None
    # Should not raise after exit


async def test_client_get_account_number_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = str(Path(tmpdir) / "test.enc")
        async with RobinhoodClient(cache_path=cache_path) as client:
            assert client.get_account_number() is None


async def test_client_restore_session_no_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = str(Path(tmpdir) / "test.enc")
        async with RobinhoodClient(cache_path=cache_path) as client:
            restored = await client.try_restore_session()
            assert not restored
