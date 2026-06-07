"""Tests for the Fernet-encrypted token cache."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from liljon.auth._token_cache import DEFAULT_SESSION, TokenCache
from liljon.auth.models import TokenData


def _make_token_data(**overrides) -> TokenData:
    defaults: dict[str, Any] = {
        "access_token": "test_access",
        "refresh_token": "test_refresh",
        "token_type": "Bearer",
        "expires_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "device_token": "dev123",
        "username": "testuser",
        "account_number": "ABC123",
    }
    defaults.update(overrides)
    return TokenData(**defaults)


def test_save_and_load():
    """Save token data, then load it back and verify fields match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = TokenCache(cache_path=str(Path(tmpdir) / "tokens.enc"), passphrase="test-pass")
        original = _make_token_data()
        cache.save(original)
        loaded = cache.load()

        assert loaded is not None
        assert loaded.access_token == original.access_token
        assert loaded.refresh_token == original.refresh_token
        assert loaded.username == original.username
        assert loaded.account_number == original.account_number


def test_load_missing():
    """Loading from a non-existent file returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = TokenCache(cache_path=str(Path(tmpdir) / "missing.enc"))
        assert cache.load() is None


def test_load_corrupted():
    """Loading corrupted data returns None rather than crashing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "bad.enc"
        path.write_text("not encrypted data")
        cache = TokenCache(cache_path=str(path))
        assert cache.load() is None


def test_load_wrong_passphrase():
    """Loading with a different passphrase returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = str(Path(tmpdir) / "tokens.enc")
        cache1 = TokenCache(cache_path=file_path, passphrase="pass1")
        cache1.save(_make_token_data())

        cache2 = TokenCache(cache_path=file_path, passphrase="pass2")
        assert cache2.load() is None


def test_delete():
    """Delete removes the cache file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "tokens.enc"
        cache = TokenCache(cache_path=str(file_path))
        cache.save(_make_token_data())
        assert file_path.exists()
        cache.delete()
        assert not file_path.exists()


def test_delete_nonexistent():
    """Deleting when file doesn't exist doesn't raise."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = TokenCache(cache_path=str(Path(tmpdir) / "none.enc"))
        cache.delete()  # Should not raise


def test_default_session_uses_legacy_path():
    """The default session stores at the base path — no migration for old tokens."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = str(Path(tmpdir) / "liljon_tokens.enc")
        legacy = TokenCache(cache_path=base)
        default = TokenCache(cache_path=base, session="default")
        implicit = TokenCache(cache_path=base)

        assert legacy.path == Path(base)
        assert default.path == Path(base)
        assert implicit.session == DEFAULT_SESSION
        assert default.path == implicit.path


def test_named_session_uses_sibling_file():
    """A named session lands next to the default file, not on top of it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = str(Path(tmpdir) / "liljon_tokens.enc")
        default = TokenCache(cache_path=base)
        trading = TokenCache(cache_path=base, session="trading")

        assert trading.session == "trading"
        assert trading.path == Path(tmpdir) / "liljon_tokens.trading.enc"
        assert trading.path != default.path


def test_sessions_are_isolated():
    """Saving one session leaves the other untouched."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = str(Path(tmpdir) / "liljon_tokens.enc")
        default = TokenCache(cache_path=base, passphrase="k")
        trading = TokenCache(cache_path=base, passphrase="k", session="trading")

        default.save(_make_token_data(username="default-user", access_token="def-tok"))
        trading.save(_make_token_data(username="trading-user", access_token="trd-tok"))

        assert default.load().username == "default-user"
        assert default.load().access_token == "def-tok"
        assert trading.load().username == "trading-user"
        assert trading.load().access_token == "trd-tok"


def test_delete_only_affects_target_session():
    """Deleting a named session keeps the default session's token in place."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = str(Path(tmpdir) / "liljon_tokens.enc")
        default = TokenCache(cache_path=base, passphrase="k")
        trading = TokenCache(cache_path=base, passphrase="k", session="trading")
        default.save(_make_token_data())
        trading.save(_make_token_data())

        trading.delete()

        assert not trading.path.exists()
        assert default.path.exists()
        assert default.load() is not None


def test_list_sessions():
    """list_sessions reports the default session first, then named ones sorted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = str(Path(tmpdir) / "liljon_tokens.enc")
        assert TokenCache.list_sessions(cache_path=base) == []

        TokenCache(cache_path=base, passphrase="k", session="zebra").save(_make_token_data())
        TokenCache(cache_path=base, passphrase="k", session="alpha").save(_make_token_data())
        TokenCache(cache_path=base, passphrase="k").save(_make_token_data())

        assert TokenCache.list_sessions(cache_path=base) == ["default", "alpha", "zebra"]


def test_list_sessions_named_only():
    """When only named sessions exist, the default is not reported."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = str(Path(tmpdir) / "liljon_tokens.enc")
        TokenCache(cache_path=base, passphrase="k", session="trading").save(_make_token_data())

        assert TokenCache.list_sessions(cache_path=base) == ["trading"]


@pytest.mark.parametrize("name", ["", "  ", None, "default"])
def test_normalize_session_defaults(name):
    """Empty/blank/None/'default' all canonicalize to the default session."""
    assert TokenCache.normalize_session(name) == DEFAULT_SESSION


@pytest.mark.parametrize("name", ["../evil", "a/b", "spaces here", "dot.name", "weird!"])
def test_invalid_session_name_rejected(name):
    """Unsafe session names raise rather than escaping the cache directory."""
    with pytest.raises(ValueError):
        TokenCache.normalize_session(name)
    with pytest.raises(ValueError):
        TokenCache(session=name)


def test_save_is_atomic():
    """If os.write crashes mid-write, original cache file is unchanged and temp file is cleaned up."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "tokens.enc"
        cache = TokenCache(cache_path=str(file_path), passphrase="test-pass")

        # Save initial data
        original = _make_token_data()
        cache.save(original)
        original_bytes = file_path.read_bytes()

        # Attempt a second save that crashes during os.write
        updated = _make_token_data(access_token="new_access")
        with patch("liljon.auth._token_cache.os.write", side_effect=OSError("disk full")):
            try:
                cache.save(updated)
            except OSError:
                pass

        # Original file should be unchanged
        assert file_path.read_bytes() == original_bytes

        # No leftover temp files in the directory
        remaining = list(Path(tmpdir).iterdir())
        assert remaining == [file_path]

        # Original data should still load correctly
        loaded = cache.load()
        assert loaded is not None
        assert loaded.access_token == "test_access"
