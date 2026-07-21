"""Team model."""

from __future__ import annotations

from ._base import Py2KModel


class Team(Py2KModel):
    team_name: str
    team_type: str | None = None
    player_count: int | None = None
    average_rating: float | None = None