"""Two-step authentication flow for Robinhood.

Implements:
1. try_restore_session() — load cached tokens, refresh if near expiry
2. login(username, password) — POST credentials, handle challenge or direct login
3. submit_verification(code) — respond to SMS/email challenge, finalize login
4. refresh() — use refresh_token to get a new access_token
5. logout() — clear transport auth + delete cache
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon.auth._device_token import generate_device_token
from liljon.auth._token_cache import TokenCache
from liljon.auth.models import ChallengeInfo, LoginResult, TokenData
from liljon.exceptions import APIError, AuthenticationError

logger = logging.getLogger(__name__)

ROBINHOOD_CLIENT_ID = "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS"
SMS_POLL_TIMEOUT = 120
SMS_POLL_INTERVAL = 5
WORKFLOW_POLL_TIMEOUT = 120
WORKFLOW_POLL_RETRIES = 5


class AuthFlow:
    """Manages the full Robinhood authentication lifecycle."""

    def __init__(self, transport: HttpTransport, token_cache: TokenCache) -> None:
        self._transport = transport
        self._cache = token_cache
        self._token_data: TokenData | None = None
        self._device_token: str | None = None
        # Stored between login() and submit_verification()
        self._pending_login_payload: dict | None = None
        self._pending_challenge: ChallengeInfo | None = None
        self._pending_username: str | None = None

    @property
    def token_data(self) -> TokenData | None:
        return self._token_data

    async def try_restore_session(self) -> bool:
        """Attempt to restore a session from the encrypted token cache.

        Returns True if the session is valid (refreshing the token if needed).
        """
        token_data = self._cache.load()
        if token_data is None:
            return False

        self._transport.set_auth(token_data.token_type, token_data.access_token)

        # Check if the token is near expiry and refresh
        if token_data.expires_at and token_data.expires_at < datetime.now(timezone.utc) + timedelta(minutes=5):
            logger.info("Token near expiry, attempting refresh")
            try:
                await self._refresh(token_data)
                return True
            except Exception:
                logger.debug("Token refresh failed, trying cached token as-is")

        # Validate by making a lightweight request
        try:
            await self._transport.get(ep.positions(), params={"nonzero": "true"})
            self._token_data = token_data
            logger.info("Session restored for %s", token_data.username)
            return True
        except Exception:
            logger.debug("Cached session invalid, clearing auth")
            self._transport.clear_auth()
            return False

    async def login(self, username: str, password: str) -> LoginResult:
        """Phase 1: Send credentials. Returns immediately if direct login succeeds,
        or returns challenge_required if 2FA is needed.
        """
        device_token = generate_device_token()
        self._device_token = device_token

        login_payload = {
            "client_id": ROBINHOOD_CLIENT_ID,
            "expires_in": 86400,
            "grant_type": "password",
            "password": password,
            "scope": "internal",
            "username": username,
            "device_token": device_token,
            "try_passkeys": False,
            "token_request_path": "/login",
            "create_read_only_secondary_token": True,
        }

        data = await self._transport.post(ep.login(), data=login_payload, raise_on_error=False)

        # Check for error in response body
        if "error" in data:
            detail = data.get("detail", data.get("error_description", data["error"]))
            raise AuthenticationError(f"Robinhood login error: {detail}")

        # Direct login success
        if "access_token" in data:
            self._finalize(data, login_payload, username)
            return LoginResult(status="logged_in", message=f"Logged in as {username}", username=username)

        # Verification workflow required
        if "verification_workflow" not in data:
            raise AuthenticationError(f"Unexpected Robinhood response: {list(data.keys())}")

        workflow_id = data["verification_workflow"]["id"]
        logger.info("Verification workflow triggered: %s", workflow_id)

        # Start the pathfinder machine verification
        machine_payload = {"device_id": device_token, "flow": "suv", "input": {"workflow_id": workflow_id}}
        try:
            machine_data = await self._transport.post(ep.pathfinder_user_machine(), json=machine_payload)
        except APIError as exc:
            raise AuthenticationError(f"Failed to initiate verification: {exc.detail}") from exc

        if "id" not in machine_data:
            raise AuthenticationError("Failed to initiate verification workflow with Robinhood")

        machine_id = machine_data["id"]

        # Poll until the SMS/email challenge is issued
        challenge_info = await self._poll_for_challenge(machine_id)

        # Store state for submit_verification()
        self._pending_login_payload = login_payload
        self._pending_challenge = challenge_info
        self._pending_username = username

        return LoginResult(
            status="challenge_required",
            message=f"Verification code sent via {challenge_info.challenge_type}. Enter the code to continue.",
            challenge=challenge_info,
        )

    async def submit_verification(self, code: str) -> LoginResult:
        """Phase 2: Submit verification code and complete login."""
        if not self._pending_challenge or not self._pending_login_payload:
            return LoginResult(status="error", message="No pending challenge. Call login() first.")

        challenge = self._pending_challenge

        # POST verification code
        try:
            resp = await self._transport.post(
                ep.challenge_respond(challenge.challenge_id),
                data={"response": code},
            )
        except APIError as exc:
            return LoginResult(status="error", message=f"Failed to submit verification code: {exc.detail}")

        if resp.get("status") != "validated":
            return LoginResult(status="invalid_code", message="Invalid verification code. Please try again.")

        # Poll workflow for approval
        await self._poll_workflow_approval(challenge.machine_id)

        # Re-POST login payload to get access token
        data = await self._transport.post(ep.login(), data=self._pending_login_payload, raise_on_error=False)

        if "access_token" not in data:
            detail = data.get("detail", data.get("error", ""))
            return LoginResult(
                status="error",
                message=f"Failed to obtain access token after verification. {detail}".strip(),
            )

        username = self._pending_username or "unknown"
        self._finalize(data, self._pending_login_payload, username)

        # Clear pending state
        self._pending_challenge = None
        self._pending_login_payload = None
        self._pending_username = None

        return LoginResult(status="logged_in", message=f"Successfully connected as {username}", username=username)

    async def refresh(self) -> bool:
        """Refresh the access token using the stored refresh_token. Returns True on success."""
        if not self._token_data or not self._token_data.refresh_token:
            return False
        try:
            await self._refresh(self._token_data)
            return True
        except Exception:
            logger.warning("Token refresh failed", exc_info=True)
            return False

    async def logout(self) -> None:
        """Clear the session and delete the cached token."""
        self._transport.clear_auth()
        self._cache.delete()
        self._token_data = None
        self._pending_challenge = None
        self._pending_login_payload = None
        self._pending_username = None

    def get_account_number(self) -> str | None:
        """Read the account number from the current token data."""
        if self._token_data:
            return self._token_data.account_number
        # Fall back to cache
        cached = self._cache.load()
        return cached.account_number if cached else None

    def set_account_number(self, account_number: str) -> None:
        """Store the account number in token data and persist to cache."""
        if not self._token_data:
            cached = self._cache.load()
            if not cached:
                raise AuthenticationError("No active session. Log in first.")
            self._token_data = cached

        self._token_data.account_number = account_number
        self._cache.save(self._token_data)

    # ── Private helpers ─────────────────────────────────────────────────

    def _finalize(self, data: dict, login_payload: dict, username: str) -> None:
        """Set auth on transport and persist token data."""
        token_type = data.get("token_type", "Bearer")
        access_token = data["access_token"]

        self._transport.set_auth(token_type, access_token)

        expires_in = data.get("expires_in", 86400)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        self._token_data = TokenData(
            access_token=access_token,
            refresh_token=data.get("refresh_token", ""),
            token_type=token_type,
            expires_at=expires_at,
            device_token=login_payload.get("device_token", ""),
            username=username,
        )
        self._cache.save(self._token_data)
        logger.info("Login finalized and cached for %s", username)

    async def _refresh(self, token_data: TokenData) -> None:
        """Exchange refresh_token for a new access_token."""
        payload = {
            "client_id": ROBINHOOD_CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": token_data.refresh_token,
            "scope": "internal",
            "device_token": token_data.device_token or "",
        }

        data = await self._transport.post(ep.login(), data=payload, raise_on_error=False)

        if "access_token" not in data:
            detail = data.get("detail", data.get("error", str(data)))
            raise AuthenticationError(f"Token refresh failed: {detail}")

        new_token_type = data.get("token_type", "Bearer")
        self._transport.set_auth(new_token_type, data["access_token"])

        expires_in = data.get("expires_in", 86400)
        self._token_data = TokenData(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", token_data.refresh_token),
            token_type=new_token_type,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            device_token=token_data.device_token,
            username=token_data.username,
            account_number=token_data.account_number,
        )
        self._cache.save(self._token_data)
        logger.info("Token refreshed for %s", self._token_data.username)

    async def _poll_for_challenge(self, machine_id: str) -> ChallengeInfo:
        """Poll pathfinder until a SMS/email challenge is issued."""
        elapsed = 0.0
        while elapsed < SMS_POLL_TIMEOUT:
            await asyncio.sleep(SMS_POLL_INTERVAL)
            elapsed += SMS_POLL_INTERVAL

            try:
                inquiry_resp = await self._transport.get(ep.pathfinder_inquiry(machine_id))
            except APIError:
                continue

            context = inquiry_resp.get("context", {})
            challenge = context.get("sheriff_challenge")
            if not challenge:
                continue

            challenge_type = challenge["type"]
            challenge_status = challenge["status"]
            challenge_id = challenge["id"]

            if challenge_type == "prompt":
                raise AuthenticationError(
                    "Robinhood requested device approval via push notification. "
                    "Only SMS and email verification are supported. "
                    "Please enable SMS 2FA in your Robinhood app settings."
                )

            if challenge_type in ("sms", "email") and challenge_status == "issued":
                return ChallengeInfo(
                    challenge_id=challenge_id,
                    challenge_type=challenge_type,
                    machine_id=machine_id,
                    status=challenge_status,
                )

        raise AuthenticationError("Timed out waiting for SMS challenge to be issued by Robinhood")

    async def _poll_workflow_approval(self, machine_id: str) -> None:
        """Poll the verification workflow until approved or timeout."""
        elapsed = 0.0
        retries = WORKFLOW_POLL_RETRIES

        while elapsed < WORKFLOW_POLL_TIMEOUT and retries > 0:
            try:
                payload = {"sequence": 0, "user_input": {"status": "continue"}}
                resp = await self._transport.post(ep.pathfinder_inquiry(machine_id), json=payload)
                if resp and "type_context" in resp:
                    if resp["type_context"].get("result") == "workflow_status_approved":
                        return
            except Exception:
                retries -= 1

            await asyncio.sleep(3)
            elapsed += 3

        # Proceed on timeout (matches observed Robinhood behavior)
        logger.warning("Workflow approval poll timed out, proceeding with login attempt")
