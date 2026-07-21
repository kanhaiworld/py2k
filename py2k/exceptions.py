"""Exception hierarchy for py2k."""

from __future__ import annotations


class Py2KError(Exception):
    """Base exception for all py2k errors."""


class APIError(Py2KError):
    """The API returned an error response."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(APIError):
    """Missing or invalid API key (401/403)."""


class NotFoundError(APIError):
    """The requested resource does not exist (404)."""


class RateLimitError(APIError):
    """Rate limit exceeded (429). `retry_after` is in seconds, if provided."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=status_code, details=details)
        self.retry_after = retry_after
