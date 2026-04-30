"""Capture Robinhood login XHRs — focused on the device-approval (push) flow.

Opens a fresh Chromium window (no cached profile) so the full login workflow
runs end to end. You log in normally; when Robinhood asks to verify on the
mobile app, approve the push prompt on your phone. Every request to *.robinhood.com
that is part of auth (oauth2, challenge, pathfinder, sherwood/users) is recorded
into capture_login.jsonl with passwords/tokens redacted.

Usage:
    cd /home/jchappo/code/liljon
    uv run --with playwright python scripts/capture_login.py
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import Response, async_playwright

OUTFILE = Path("scripts/capture_login.jsonl")

CAPTURE_PATTERNS = [
    re.compile(r"api\.robinhood\.com/(oauth2|challenge|pathfinder|sherwood|users|user)"),
    re.compile(r"api\.robinhood\.com/.*/2fa", re.IGNORECASE),
    re.compile(r"sherwood\.robinhood\.com"),
]

REDACT_KEYS = {
    "password",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "set-cookie",
    "id_token",
    "secondary_token",
}


def should_capture(url: str) -> bool:
    return any(p.search(url) for p in CAPTURE_PATTERNS)


def redact(obj):
    if isinstance(obj, dict):
        return {
            k: ("<REDACTED>" if k.lower() in REDACT_KEYS else redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


async def main() -> None:
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text("")
    print("=" * 70)
    print("  ROBINHOOD LOGIN CAPTURE — push-notification (prompt) flow")
    print("=" * 70)
    print()
    print(f"  Output: {OUTFILE.resolve()}")
    print()
    print("  1. Chromium will open with a clean profile.")
    print("  2. Click 'Log in' on robinhood.com and enter your credentials.")
    print("  3. When prompted, approve on your phone (Robinhood app push).")
    print("  4. Once logged in fully, close the browser window.")
    print()
    print("  Passwords and tokens are redacted before being written.")
    print("=" * 70)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await ctx.new_page()

        async def on_response(response: Response) -> None:
            url = response.url
            if not should_capture(url):
                return

            entry: dict = {
                "ts": datetime.now().isoformat(),
                "method": response.request.method,
                "url": url,
                "status": response.status,
                "request_headers": {},
                "request_body": None,
                "response_headers": {},
                "response_body": None,
            }

            try:
                req_headers = await response.request.all_headers()
                entry["request_headers"] = {
                    k: ("<REDACTED>" if k.lower() in REDACT_KEYS else v)
                    for k, v in req_headers.items()
                    if k.lower()
                    in (
                        "authorization",
                        "content-type",
                        "accept",
                        "x-robinhood-api-version",
                        "x-hyper-ex",
                        "origin",
                        "referer",
                        "cookie",
                    )
                }
            except Exception:
                pass

            try:
                post_data = response.request.post_data
                if post_data:
                    try:
                        entry["request_body"] = redact(json.loads(post_data))
                    except (json.JSONDecodeError, TypeError):
                        # form-encoded — parse k=v&k=v
                        if "=" in post_data and "&" in post_data:
                            try:
                                from urllib.parse import parse_qs

                                parsed = {
                                    k: v[0] if len(v) == 1 else v
                                    for k, v in parse_qs(post_data).items()
                                }
                                entry["request_body"] = redact(parsed)
                            except Exception:
                                entry["request_body"] = "<unparseable form body>"
                        else:
                            entry["request_body"] = post_data
            except Exception:
                pass

            try:
                resp_headers = await response.all_headers()
                entry["response_headers"] = {
                    k: ("<REDACTED>" if k.lower() in REDACT_KEYS else v)
                    for k, v in resp_headers.items()
                    if k.lower()
                    in (
                        "content-type",
                        "x-request-id",
                        "set-cookie",
                    )
                }
            except Exception:
                pass

            try:
                body = await response.body()
                if body:
                    try:
                        entry["response_body"] = redact(json.loads(body))
                    except (json.JSONDecodeError, TypeError):
                        entry["response_body"] = body.decode(
                            "utf-8", errors="replace"
                        )[:2000]
            except Exception:
                pass

            with OUTFILE.open("a") as f:
                f.write(json.dumps(entry, default=str) + "\n")

            short = url.split("robinhood.com", 1)[-1]
            color = "\033[92m" if response.status < 400 else "\033[91m"
            print(f"  [{entry['method']:4s}] {color}{response.status}\033[0m {short}")

        page.on("response", on_response)

        await page.goto("https://robinhood.com/login")
        print("\n  Browser open. Log in now.\n")

        try:
            await page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        try:
            await ctx.wait_for_event("close", timeout=5000)
        except Exception:
            pass

    print(f"\n  Capture saved to {OUTFILE.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
