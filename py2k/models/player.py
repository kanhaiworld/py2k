"""Player and badge models."""

from __future__ import annotations

from typing import Any

from ._base import Py2KModel


class Badge(Py2KModel):
    name: str | None = None
    slug: str | None = None
    tier: str | None = None


class PlayerSummary(Py2KModel):
    """Shape returned by /players, /players/bulk, /players/search, and rosters."""

    name: str
    slug: str
    team: str | None = None
    team_type: str | None = None
    overall: int | None = None
    positions: list[str] = []
    player_image: str | None = None
    team_img: str | None = None


class Player(PlayerSummary):
    """Full detail, as returned by /players/slug/:slug."""

    tier: str | None = None
    archetype: str | None = None
    height: str | None = None
    weight: str | None = None
    attributes: dict[str, int] = {}
    badges: list[Badge] | dict[str, Any] = {}
    hot_zones: dict[str, Any] | None = None
