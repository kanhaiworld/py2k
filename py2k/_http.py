"""Low-level HTTP plumbing: auth header, retry-on-429, rate-limit tracking,
and mapping API error responses to exceptions. Endpoint methods live in
client.py; this module knows nothing about players/teams."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests

from .exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)

DEFAULT_BASE_URL = "https://api.nba2kapi.com/api"


@dataclass
class RateLimitInfo:
    limit: int | None = None
    remaining: int | None = None
    reset: str | None = None

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> "RateLimitInfo":
        def _int(value: str | None) -> int | None:
            return int(value) if value is not None else None

        return cls(
            limit=_int(headers.get("X-RateLimit-Limit")),
            remaining=_int(headers.get("X-RateLimit-Remaining")),
            reset=headers.get("X-RateLimit-Reset"),
        )


def clean_params(**params: Any) -> dict[str, Any]:
    """Drop None values and comma-join list/tuple values for query params."""
    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            value = ",".join(str(v) for v in value)
        cleaned[key] = value
    return cleaned


class HTTPClient:
    """Owns the requests.Session, auth header, retry loop, and error mapping."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        auto_retry_rate_limit: bool = True,
        max_retries: int = 2,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auto_retry_rate_limit = auto_retry_rate_limit
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.rate_limit = RateLimitInfo()

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None) -> dict:
        url = f"{self.base_url}{path}"
        headers = {"X-API-Key": self.api_key}
        attempt = 0
        while True:
            response = self.session.request(
                method, url, params=params, headers=headers, timeout=self.timeout
            )
            self.rate_limit = RateLimitInfo.from_headers(response.headers)

            if response.status_code == 429 and self.auto_retry_rate_limit and attempt < self.max_retries:
                time.sleep(self._retry_after_seconds(response))
                attempt += 1
                continue

            return self._parse(response)

    @staticmethod
    def _retry_after_seconds(response: requests.Response) -> float:
        try:
            details = response.json().get("error", {}).get("details", {})
            if "retryAfter" in details:
                return float(details["retryAfter"])
        except (ValueError, AttributeError):
            pass
        return float(response.headers.get("Retry-After", 1))

    @staticmethod
    def _parse(response: requests.Response) -> dict:
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        if response.ok and payload.get("success", True):
            return payload

        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        message = error.get("message", response.text or f"HTTP {response.status_code}")
        code = error.get("code")
        details = error.get("details", {})

        if response.status_code in (401, 403):
            raise AuthenticationError(message, code=code, status_code=response.status_code, details=details)
        if response.status_code == 404:
            raise NotFoundError(message, code=code, status_code=response.status_code, details=details)
        if response.status_code == 429:
            raise RateLimitError(
                message,
                code=code,
                status_code=response.status_code,
                details=details,
                retry_after=details.get("retryAfter"),
            )
        raise APIError(message, code=code, status_code=response.status_code, details=details)

    def close(self) -> None:
        self.session.close()