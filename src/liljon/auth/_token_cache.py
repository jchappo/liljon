"""Fernet-encrypted JSON token storage.

Replaces the insecure pickle-based storage from robin_stocks.
Key is derived from an optional passphrase or machine-specific data.

Sessions
--------
A *session* is a named instance of a stored token. Multiple sessions can live
side by side on the same machine — each is a separate encrypted file in the
cache directory. The ``default`` session is stored at the original location
(``~/.tokens/liljon_tokens.enc``) so tokens written before sessions existed keep
loading unchanged; named sessions are stored as siblings next to it
(``~/.tokens/liljon_tokens.<name>.enc``).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import re
import tempfile
from base64 import urlsafe_b64encode
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from liljon.auth.models import TokenData

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".tokens")
_DEFAULT_CACHE_FILE = "liljon_tokens.enc"

#: Session used when the caller doesn't name one. The default session is stored
#: at the original cache path, so pre-session tokens load without migration.
DEFAULT_SESSION = "default"

#: Session names become filenames, so restrict them to a filesystem-safe set.
#: This also keeps them unambiguous against the ``<stem>.<session><suffix>``
#: layout used to derive per-session paths.
_SESSION_NAME_RE = re.compile(r"[A-Za-z0-9_-]+")


def _normalize_session(session: str | None) -> str:
    """Validate a session name, returning the canonical default when unset."""
    if session is None:
        return DEFAULT_SESSION
    session = session.strip()
    if not session or session == DEFAULT_SESSION:
        return DEFAULT_SESSION
    if not _SESSION_NAME_RE.fullmatch(session):
        raise ValueError(
            f"Invalid session name {session!r}: use only letters, digits, '-', and '_'."
        )
    return session


def _resolve_session_path(base: Path, session: str) -> Path:
    """Map a session name onto a cache file relative to the default ``base`` file."""
    if session == DEFAULT_SESSION:
        return base
    return base.with_name(f"{base.stem}.{session}{base.suffix}")


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
    """Encrypt, store, and restore TokenData as JSON using Fernet.

    Each instance is bound to a single session (default: ``"default"``). The
    encryption key is shared across sessions on a machine — sessions are
    distinguished by file, not by key.
    """

    def __init__(
        self,
        cache_path: str | None = None,
        passphrase: str | None = None,
        session: str | None = None,
    ) -> None:
        self._session = _normalize_session(session)
        base = Path(cache_path) if cache_path else Path(_DEFAULT_CACHE_DIR) / _DEFAULT_CACHE_FILE
        self._path = _resolve_session_path(base, self._session)
        self._fernet = Fernet(_derive_key(passphrase))

    @property
    def path(self) -> Path:
        return self._path

    @property
    def session(self) -> str:
        """The session this cache reads from and writes to."""
        return self._session

    @staticmethod
    def normalize_session(session: str | None) -> str:
        """Validate/canonicalize a session name (raises ValueError if invalid)."""
        return _normalize_session(session)

    @classmethod
    def list_sessions(cls, cache_path: str | None = None) -> list[str]:
        """Return the session names that have a cached token on disk.

        The default session (if present) is listed first; named sessions follow
        in alphabetical order. Returns an empty list if the cache directory
        doesn't exist yet.
        """
        base = Path(cache_path) if cache_path else Path(_DEFAULT_CACHE_DIR) / _DEFAULT_CACHE_FILE
        directory = base.parent
        if not directory.is_dir():
            return []

        prefix = f"{base.stem}."
        found: set[str] = set()
        for entry in directory.iterdir():
            if not entry.is_file():
                continue
            if entry.name == base.name:
                found.add(DEFAULT_SESSION)
            elif entry.name.startswith(prefix) and entry.suffix == base.suffix:
                name = entry.name[len(prefix):]
                if base.suffix:
                    name = name[: -len(base.suffix)]
                if _SESSION_NAME_RE.fullmatch(name):
                    found.add(name)

        ordered: list[str] = []
        if DEFAULT_SESSION in found:
            ordered.append(DEFAULT_SESSION)
            found.discard(DEFAULT_SESSION)
        ordered.extend(sorted(found))
        return ordered

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
        logger.info("Token data saved to %s (session=%s)", self._path, self._session)

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
        """Remove the cached token file for this session."""
        if self._path.is_file():
            self._path.unlink()
            logger.info("Token cache deleted at %s (session=%s)", self._path, self._session)
