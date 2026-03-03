"""RobinhoodClient: the main entry point composing all API namespaces.

Usage:
    async with RobinhoodClient() as client:
        result = await client.login("user@email.com", "password")
        if result.status == "challenge_required":
            code = await get_code_from_ui()
            result = await client.submit_verification(code)
        quotes = await client.stocks.get_quotes(["AAPL", "MSFT"])
"""

from __future__ import annotations

from liljon._http import HttpTransport
from liljon.api.account import AccountAPI
from liljon.api.alerts import AlertsAPI
from liljon.api.crypto import CryptoAPI
from liljon.api.discovery import DiscoveryAPI
from liljon.api.futures import FuturesAPI
from liljon.api.indexes import IndexesAPI
from liljon.api.markets import MarketsAPI
from liljon.api.options import OptionsAPI
from liljon.api.orders import OrdersAPI
from liljon.api.screeners import ScreenersAPI
from liljon.api.stocks import StocksAPI
from liljon.auth._flow import AuthFlow
from liljon.auth._token_cache import TokenCache
from liljon.auth.models import LoginResult


class RobinhoodClient:
    """Async-first Robinhood API client.

    All state is instance-scoped — no global session, no module-level flags.
    Multiple client instances can coexist for different accounts.
    """

    def __init__(
        self,
        cache_path: str | None = None,
        passphrase: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._transport = HttpTransport(timeout)
        self._token_cache = TokenCache(cache_path, passphrase)
        self._auth = AuthFlow(self._transport, self._token_cache)

        # API namespaces
        self.alerts = AlertsAPI(self._transport)
        self.stocks = StocksAPI(self._transport)
        self.options = OptionsAPI(self._transport)
        self.crypto = CryptoAPI(self._transport)
        self.futures = FuturesAPI(self._transport)
        self.indexes = IndexesAPI(self._transport)
        self.account = AccountAPI(self._transport)
        self.orders = OrdersAPI(self._transport)
        self.markets = MarketsAPI(self._transport)
        self.screeners = ScreenersAPI(self._transport)
        self.discovery = DiscoveryAPI(self._transport)

    # ── Auth delegation ─────────────────────────────────────────────────

    async def login(self, username: str, password: str) -> LoginResult:
        """Phase 1: Send credentials. Returns LoginResult with status and challenge info if 2FA required."""
        return await self._auth.login(username, password)

    async def submit_verification(self, code: str) -> LoginResult:
        """Phase 2: Submit SMS/email verification code to complete login."""
        return await self._auth.submit_verification(code)

    async def try_restore_session(self) -> bool:
        """Attempt to restore a session from the encrypted token cache."""
        return await self._auth.try_restore_session()

    async def refresh_token(self) -> bool:
        """Refresh the access token using the stored refresh_token."""
        return await self._auth.refresh()

    async def logout(self) -> None:
        """Clear the session and delete the cached token."""
        await self._auth.logout()

    @property
    def is_authenticated(self) -> bool:
        """Check if the transport has an active auth header."""
        return self._transport.is_authenticated

    def get_account_number(self) -> str | None:
        """Read the stored account number."""
        return self._auth.get_account_number()

    def set_account_number(self, account_number: str) -> None:
        """Store the account number in the token cache."""
        self._auth.set_account_number(account_number)

    # ── Lifecycle ───────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._transport.close()

    async def __aenter__(self) -> RobinhoodClient:
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
