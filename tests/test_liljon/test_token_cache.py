"""Tests for the Fernet-encrypted token cache."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from liljon.auth._token_cache import TokenCache
from liljon.auth.models import TokenData


def _make_token_data(**overrides) -> TokenData:
    defaults = {
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
