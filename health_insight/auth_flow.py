"""Fitbit OAuth helper to obtain initial refresh tokens.

This module starts a localhost redirect listener, opens the Fitbit authorization
page for the requested scopes, captures the authorization code, exchanges it for
access/refresh tokens, and optionally persists them into an env file.
"""
from __future__ import annotations

import argparse
import base64
import os
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Iterable, Optional

import requests

BASE_AUTHORIZE_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"
DEFAULT_REDIRECT_PATH = "/callback"


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def build_authorize_url(client_id: str, redirect_uri: str, scopes: Iterable[str]) -> str:
    """Create the Fitbit authorization URL for the given scopes."""

    scope_str = " ".join(scopes)
    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope_str,
        }
    )
    return f"{BASE_AUTHORIZE_URL}?{query}"


def _start_redirect_listener(port: int, timeout: int, redirect_path: str) -> str:
    """Start a local HTTP listener to capture the OAuth authorization code."""

    code_container: Dict[str, str] = {}
    event = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # type: ignore[override]
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if parsed.path == redirect_path and "code" in params:
                code_container["code"] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h2>Fitbit auth complete.</h2><p>You can close this tab.</p></body></html>"
                )
                event.set()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args) -> None:
            return

    server = HTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    event.wait(timeout=timeout)
    server.shutdown()
    thread.join()
    server.server_close()

    if not event.is_set():
        raise TimeoutError("Timed out waiting for Fitbit redirect; no authorization code captured.")
    return code_container["code"]


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str, redirect_uri: str) -> Dict:
    """Exchange an authorization code for Fitbit OAuth tokens."""

    headers = {
        "Authorization": f"Basic {_basic_auth_header(client_id, client_secret)}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    response = requests.post(TOKEN_URL, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()


def persist_tokens(env_path: Path, tokens: Dict, client_id: str, client_secret: str) -> None:
    """Update the env file with Fitbit credentials."""

    existing: Dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if not line or line.strip().startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                existing[key] = value

    existing.update(
        {
            "FITBIT_CLIENT_ID": client_id,
            "FITBIT_CLIENT_SECRET": client_secret,
            "FITBIT_REFRESH_TOKEN": tokens.get("refresh_token", ""),
            "FITBIT_ACCESS_TOKEN": tokens.get("access_token", ""),
        }
    )

    content = "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n"
    env_path.write_text(content)


def run_auth_flow(
    *,
    client_id: str,
    client_secret: str,
    scopes: Iterable[str],
    port: int = 8585,
    redirect_path: str = DEFAULT_REDIRECT_PATH,
    timeout: int = 300,
    env_file: Optional[str] = ".env",
) -> Dict:
    """Perform the full OAuth dance and optionally persist credentials."""

    redirect_uri = f"http://localhost:{port}{redirect_path}"
    url = build_authorize_url(client_id, redirect_uri, scopes)

    print("Opening browser for Fitbit authorization...")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Scopes: {' '.join(scopes)}")
    webbrowser.open(url)
    print("If the browser does not open, paste this URL manually:")
    print(url)

    code = _start_redirect_listener(port=port, timeout=timeout, redirect_path=redirect_path)
    print("Authorization code captured. Exchanging for tokens...")

    tokens = exchange_code_for_tokens(client_id, client_secret, code, redirect_uri)
    print("Received tokens:")
    print(tokens)

    if env_file:
        env_path = Path(env_file)
        persist_tokens(env_path, tokens, client_id, client_secret)
        print(f"Updated credentials in {env_path.resolve()}")

    return tokens


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Fitbit OAuth flow and save tokens.")
    parser.add_argument("--client-id", default=os.getenv("FITBIT_CLIENT_ID"), help="Fitbit application client id.")
    parser.add_argument(
        "--client-secret",
        default=os.getenv("FITBIT_CLIENT_SECRET"),
        help="Fitbit application client secret.",
    )
    parser.add_argument(
        "--scopes",
        nargs="+",
        default=["activity", "heartrate", "sleep"],
        help="One or more Fitbit scopes (space separated).",
    )
    parser.add_argument("--port", type=int, default=8585, help="Local port for the redirect listener.")
    parser.add_argument(
        "--redirect-path",
        default=DEFAULT_REDIRECT_PATH,
        help="Path portion of the redirect URI (default: /callback).",
    )
    parser.add_argument("--timeout", type=int, default=300, help="Seconds to wait for the OAuth redirect.")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Env file to update with the resulting tokens (set empty to skip writing).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.client_id or not args.client_secret:
        raise SystemExit("FITBIT_CLIENT_ID and FITBIT_CLIENT_SECRET are required (pass flags or set env vars).")

    run_auth_flow(
        client_id=args.client_id,
        client_secret=args.client_secret,
        scopes=args.scopes,
        port=args.port,
        redirect_path=args.redirect_path,
        timeout=args.timeout,
        env_file=args.env_file or None,
    )


if __name__ == "__main__":
    main()
