"""py2k: unofficial Python client for the NBA 2K API (nba2kapi.com)."""

from .client import NBA2KClient
from .exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    Py2KError,
    RateLimitError,
)
from .models import Badge, Player, PlayerSummary, Team

__all__ = [
    "NBA2KClient",
    "Py2KError",
    "APIError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "Player",
    "PlayerSummary",
    "Team",
    "Badge",
]

__version__ = "0.1.0"
