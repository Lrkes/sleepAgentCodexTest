"""Minimal Fitbit Web API client helpers.

These utilities manage token refresh and fetch daily Fitbit data so it can be
merged with the JSON storage helpers in this package.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import requests

from .storage import write_fitbit_data

BASE_URL = "https://api.fitbit.com"


@dataclass
class FitbitAuth:
    """Container for Fitbit OAuth2 credentials."""

    client_id: str
    client_secret: str
    refresh_token: str
    access_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> "FitbitAuth":
        """Load credentials from environment variables.

        Expected variables:
        - FITBIT_CLIENT_ID
        - FITBIT_CLIENT_SECRET
        - FITBIT_REFRESH_TOKEN
        - FITBIT_ACCESS_TOKEN (optional; will be refreshed if missing or expired)
        """

        import os

        client_id = os.getenv("FITBIT_CLIENT_ID")
        client_secret = os.getenv("FITBIT_CLIENT_SECRET")
        refresh_token = os.getenv("FITBIT_REFRESH_TOKEN")
        access_token = os.getenv("FITBIT_ACCESS_TOKEN")
        if not client_id or not client_secret or not refresh_token:
            raise ValueError("Missing required Fitbit env vars: FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET, FITBIT_REFRESH_TOKEN")
        return cls(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token, access_token=access_token)

    def basic_auth_header(self) -> str:
        """Return the value for the HTTP Basic Authorization header."""

        raw = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        return base64.b64encode(raw).decode("ascii")


class FitbitClient:
    """Small helper for refreshing tokens and fetching Fitbit resources."""

    def __init__(self, auth: FitbitAuth, session: Optional[requests.Session] = None):
        self.auth = auth
        self.session = session or requests.Session()

    def refresh_access_token(self, on_update: Optional[Callable[[Dict], None]] = None) -> Dict:
        """Refresh the OAuth access token using the stored refresh token.

        If provided, ``on_update`` is called with the full JSON token response so the
        caller can persist the new ``access_token`` and ``refresh_token``.
        """

        headers = {
            "Authorization": f"Basic {self.auth.basic_auth_header()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {"grant_type": "refresh_token", "refresh_token": self.auth.refresh_token}
        resp = self.session.post(f"{BASE_URL}/oauth2/token", headers=headers, data=payload)
        resp.raise_for_status()
        token_data = resp.json()
        self.auth.access_token = token_data.get("access_token")
        self.auth.refresh_token = token_data.get("refresh_token", self.auth.refresh_token)
        if on_update:
            on_update(token_data)
        return token_data

    def _auth_headers(self) -> Dict[str, str]:
        if not self.auth.access_token:
            self.refresh_access_token()
        return {"Authorization": f"Bearer {self.auth.access_token}"}

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        url = f"{BASE_URL}{path}"
        resp = self.session.get(url, headers=self._auth_headers(), params=params)
        if resp.status_code == 401:
            # token likely expired; refresh and retry once
            self.refresh_access_token()
            resp = self.session.get(url, headers=self._auth_headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def get_daily_activity(self, date_str: str) -> Dict:
        """Fetch daily activity summary for a date (YYYY-MM-DD)."""

        return self._get(f"/1/user/-/activities/date/{date_str}.json")

    def get_sleep_log(self, date_str: str) -> Dict:
        """Fetch sleep logs for a date (YYYY-MM-DD)."""

        return self._get(f"/1.2/user/-/sleep/date/{date_str}.json")

    def get_hrv_summary(self, date_str: str) -> Dict:
        """Fetch HRV summary for a date (YYYY-MM-DD)."""

        return self._get(f"/1/user/-/hrv/date/{date_str}.json")

    def fetch_daily_bundle(self, date_str: str) -> Dict:
        """Fetch activity, sleep, and HRV data for a single date."""

        return {
            "activity": self.get_daily_activity(date_str),
            "sleep": self.get_sleep_log(date_str),
            "hrv": self.get_hrv_summary(date_str),
        }

    def fetch_and_store_daily(self, date_str: str) -> Dict:
        """Fetch Fitbit data for a date and merge it into local storage."""

        bundle = self.fetch_daily_bundle(date_str)
        write_fitbit_data(date_str, bundle)
        return bundle


__all__ = [
    "FitbitAuth",
    "FitbitClient",
    "BASE_URL",
]
