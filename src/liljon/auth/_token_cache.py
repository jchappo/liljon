"""Fernet-encrypted JSON token storage.

Replaces the insecure pickle-based storage from robin_stocks.
Key is derived from an optional passphrase or machine-specific data.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import tempfile
from base64 import urlsafe_b64encode
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from liljon.auth.models import TokenData

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".tokens")
_DEFAULT_CACHE_FILE = "liljon_tokens.enc"


def _get_username() -> str:
    """Best-effort username for key derivation (works in non-terminal environments)."""
    try:
        return os.getlogin()
    except OSError:
        pass
    return os.environ.get("USER", os.environ.get("USERNAME", "user"))


def _derive_key(passphrase: str | None = None) -> bytes:
    """Derive a 32-byte Fernet key from passphrase or machine identity."""
    if passphrase:
        seed = passphrase.encode()
    else:
        identity = f"{platform.node()}:{_get_username()}:{platform.system()}"
        seed = identity.encode()

    digest = hashlib.sha256(seed).digest()
    return urlsafe_b64encode(digest)


class TokenCache:
    """Encrypt, store, and restore TokenData as JSON using Fernet."""

    def __init__(self, cache_path: str | None = None, passphrase: str | None = None) -> None:
        if cache_path:
            self._path = Path(cache_path)
        else:
            self._path = Path(_DEFAULT_CACHE_DIR) / _DEFAULT_CACHE_FILE
        self._fernet = Fernet(_derive_key(passphrase))

    @property
    def path(self) -> Path:
        return self._path

    def save(self, token_data: TokenData) -> None:
        """Encrypt and write token data to disk using atomic write-then-rename."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = token_data.model_dump_json()
        encrypted = self._fernet.encrypt(payload.encode())
        # Atomic write: write to temp file in same dir, then rename.
        # os.replace() is atomic on POSIX (and Windows as of Python 3.3+),
        # so the cache file is never left in a half-written state.
        fd, tmp_path = tempfile.mkstemp(dir=self._path.parent)
        try:
            os.write(fd, encrypted)
            os.close(fd)
            os.replace(tmp_path, self._path)
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        logger.info("Token data saved to %s", self._path)

    def load(self) -> TokenData | None:
        """Load and decrypt token data from disk. Returns None if missing or corrupted."""
        if not self._path.is_file():
            return None
        try:
            encrypted = self._path.read_bytes()
            decrypted = self._fernet.decrypt(encrypted)
            data = json.loads(decrypted)
            return TokenData(**data)
        except (InvalidToken, json.JSONDecodeError, KeyError) as exc:
            logger.warning("Failed to load token cache at %s: %s", self._path, exc)
            return None

    def delete(self) -> None:
        """Remove the cached token file."""
        if self._path.is_file():
            self._path.unlink()
            logger.info("Token cache deleted at %s", self._path)
