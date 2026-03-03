"""Launch Robinhood in Playwright with DevTools open and full network capture.

Captures complete request/response bodies for all Robinhood API endpoints.
Opens DevTools console automatically for live debugging.

Usage:
    python scripts/rh_full_capture.py

Browse as many pages as possible to capture endpoints:
    - Home / Portfolio
    - Individual stock pages (GME, AAPL, TSLA, etc.)
    - Options chains
    - Crypto pages
    - Futures
    - Screeners
    - Account settings
    - Order history
    - Watchlists
    - Index pages (S&P 500, VIX, etc.)

Close the browser when done. Results saved to scripts/rh_full_capture_results.json
"""

import asyncio
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from playwright.async_api import async_playwright

CAPTURE_DOMAINS = [
    re.compile(r"api\.robinhood\.com"),
    re.compile(r"bonfire\.robinhood\.com"),
    re.compile(r"nummus\.robinhood\.com"),
    re.compile(r"midlands\.robinhood\.com"),
    re.compile(r"dora\.robinhood\.com"),
    re.compile(r"minerva\.robinhood\.com"),
]

# Skip these noisy endpoints that are just analytics/telemetry
SKIP_PATTERNS = [
    re.compile(r"/goku/"),  # analytics
    re.compile(r"/live_frontend_log"),  # telemetry
    re.compile(r"\.png|\.jpg|\.svg|\.woff|\.css|\.js$"),  # static assets
]

captured: list[dict] = []
seen_endpoints: set[str] = set()
stats = {"total": 0, "unique": 0, "errors": 0, "with_body": 0}


def should_capture(url: str) -> bool:
    if any(p.search(url) for p in SKIP_PATTERNS):
        return False
    return any(p.search(url) for p in CAPTURE_DOMAINS)


def clean_url(url: str) -> str:
    """Strip query params for endpoint identification."""
    return url.split("?")[0]


def extract_params(url: str) -> dict:
    """Parse query string into a dict."""
    parsed = urlparse(url)
    return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}


async def main():
    output_file = Path("scripts/rh_full_capture_results.json")
    user_data_dir = Path.home() / ".playwright-rh-profile"

    print("=" * 70)
    print("  ROBINHOOD FULL API CAPTURE — with DevTools Console")
    print("=" * 70)
    print()
    print("  This will open Chromium with DevTools. Log in and browse:")
    print("  - Home page / Portfolio")
    print("  - Stock detail pages (try GME, AAPL, TSLA, SPY)")
    print("  - Options chains on a stock page")
    print("  - Crypto page (BTC, ETH)")
    print("  - Index pages (VIX, S&P 500)")
    print("  - Account / Order History / Statements")
    print("  - Screeners")
    print("  - Watchlists")
    print("  - Futures (if enabled)")
    print("  - Settings / Subscription")
    print()
    print("  Close the browser window when done capturing.")
    print("=" * 70)
    print()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(user_data_dir),
            headless=False,
            viewport={"width": 1600, "height": 1000},
            args=[
                "--auto-open-devtools-for-tabs",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        page = context.pages[0] if context.pages else await context.new_page()

        async def on_response(response):
            url = response.url
            if not should_capture(url):
                return

            stats["total"] += 1
            method = response.request.method
            endpoint = clean_url(url)
            endpoint_key = f"{method} {endpoint}"
            is_new = endpoint_key not in seen_endpoints

            if is_new:
                seen_endpoints.add(endpoint_key)
                stats["unique"] += 1

            entry = {
                "timestamp": datetime.now().isoformat(),
                "method": method,
                "url": url,
                "endpoint": endpoint,
                "params": extract_params(url),
                "status": response.status,
                "resource_type": response.request.resource_type,
                "request_headers": {},
                "request_body": None,
                "response_body": None,
                "response_headers": {},
                "is_new_endpoint": is_new,
            }

            # Capture request headers (filter to useful ones)
            try:
                req_headers = response.request.headers
                useful_headers = {
                    k: v
                    for k, v in req_headers.items()
                    if k.lower()
                    in (
                        "authorization",
                        "content-type",
                        "accept",
                        "x-robinhood-api-version",
                        "x-timezone-id",
                        "origin",
                        "referer",
                    )
                }
                entry["request_headers"] = useful_headers
            except Exception:
                pass

            # Capture request POST body
            try:
                post_data = response.request.post_data
                if post_data:
                    try:
                        entry["request_body"] = json.loads(post_data)
                    except (json.JSONDecodeError, TypeError):
                        entry["request_body"] = post_data
            except Exception:
                pass

            # Capture response body
            try:
                body = await response.body()
                if body:
                    stats["with_body"] += 1
                    try:
                        json_body = json.loads(body)
                        # Truncate very large responses (keep structure, trim arrays)
                        entry["response_body"] = truncate_json(json_body, max_array=5, max_depth=4)
                        entry["response_body_full_size"] = len(body)
                    except (json.JSONDecodeError, TypeError):
                        text = body.decode("utf-8", errors="replace")[:2000]
                        entry["response_body"] = text
            except Exception:
                pass

            # Capture response headers
            try:
                resp_headers = await response.all_headers()
                entry["response_headers"] = {
                    k: v
                    for k, v in resp_headers.items()
                    if k.lower() in ("content-type", "x-request-id", "x-ratelimit-remaining")
                }
            except Exception:
                pass

            captured.append(entry)

            # Pretty print to console
            status = response.status
            star = " *** NEW ***" if is_new else ""
            color_status = f"\033[92m{status}\033[0m" if status < 400 else f"\033[91m{status}\033[0m"
            print(f"  [{method:4s}] {color_status} {endpoint}{star}")
            if entry["params"]:
                params_str = ", ".join(f"{k}={v}" for k, v in entry["params"].items())
                print(f"         ? {params_str}")

        page.on("response", on_response)

        await page.goto("https://robinhood.com/")
        print("\n  Navigated to robinhood.com — browse around to capture endpoints.\n")

        # Wait for browser to close
        try:
            await page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        try:
            await context.wait_for_event("close", timeout=5000)
        except Exception:
            pass

    # Save results
    print(f"\n{'=' * 70}")
    print(f"  CAPTURE COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Total API calls:     {stats['total']}")
    print(f"  Unique endpoints:    {stats['unique']}")
    print(f"  With response body:  {stats['with_body']}")
    print()

    if captured:
        output_file.write_text(json.dumps(captured, indent=2, default=str))
        print(f"  Full results saved to: {output_file}")

        # Also save a deduplicated summary
        summary = generate_summary(captured)
        summary_file = Path("scripts/rh_full_capture_summary.json")
        summary_file.write_text(json.dumps(summary, indent=2, default=str))
        print(f"  Endpoint summary saved to: {summary_file}")

        # Print unique endpoints grouped by domain
        print(f"\n{'=' * 70}")
        print(f"  UNIQUE ENDPOINTS BY DOMAIN")
        print(f"{'=' * 70}")
        by_domain: dict[str, list[str]] = {}
        for ep in sorted(seen_endpoints):
            method, url = ep.split(" ", 1)
            domain = urlparse(url).netloc
            by_domain.setdefault(domain, []).append(ep)

        for domain in sorted(by_domain):
            print(f"\n  --- {domain} ({len(by_domain[domain])} endpoints) ---")
            for ep in sorted(by_domain[domain]):
                print(f"    {ep}")

    else:
        print("  No API requests captured.")


def truncate_json(obj, max_array=5, max_depth=4, depth=0):
    """Truncate large JSON objects to keep file sizes manageable."""
    if depth >= max_depth:
        if isinstance(obj, dict):
            return {k: "..." for k in list(obj.keys())[:5]}
        if isinstance(obj, list):
            return [f"... ({len(obj)} items)"]
        return obj

    if isinstance(obj, dict):
        return {k: truncate_json(v, max_array, max_depth, depth + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        truncated = [truncate_json(item, max_array, max_depth, depth + 1) for item in obj[:max_array]]
        if len(obj) > max_array:
            truncated.append(f"... ({len(obj) - max_array} more items)")
        return truncated
    return obj


def generate_summary(requests: list[dict]) -> dict:
    """Generate a deduplicated endpoint summary with example request/response shapes."""
    endpoints: dict[str, dict] = {}

    for req in requests:
        key = f"{req['method']} {req['endpoint']}"

        if key not in endpoints:
            endpoints[key] = {
                "method": req["method"],
                "endpoint": req["endpoint"],
                "domain": urlparse(req["endpoint"]).netloc,
                "example_params": req["params"],
                "example_status": req["status"],
                "example_request_body": req.get("request_body"),
                "example_response_keys": None,
                "example_response_body": req.get("response_body"),
                "hit_count": 0,
                "statuses_seen": [],
                "all_params_seen": [],
            }

        ep = endpoints[key]
        ep["hit_count"] += 1
        if req["status"] not in ep["statuses_seen"]:
            ep["statuses_seen"].append(req["status"])
        if req["params"] and req["params"] not in ep["all_params_seen"]:
            ep["all_params_seen"].append(req["params"])

        # Extract response shape (top-level keys)
        body = req.get("response_body")
        if isinstance(body, dict) and ep["example_response_keys"] is None:
            ep["example_response_keys"] = list(body.keys())

    return {
        "capture_date": datetime.now().isoformat(),
        "total_requests": len(requests),
        "unique_endpoints": len(endpoints),
        "endpoints": dict(sorted(endpoints.items())),
    }


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted! Saving partial results...")
        if captured:
            output = Path("scripts/rh_full_capture_results.json")
            output.write_text(json.dumps(captured, indent=2, default=str))
            summary = generate_summary(captured)
            Path("scripts/rh_full_capture_summary.json").write_text(json.dumps(summary, indent=2, default=str))
            print(f"  Saved {len(captured)} requests to {output}")
        sys.exit(0)
