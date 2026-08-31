"""NBA2KClient: the public, endpoint-oriented facade over the NBA 2K API.

Auth, retries, rate limits, and error mapping live in `_http.py`; this
module only knows about players/teams and how to turn responses into models.
"""

from __future__ import annotations

import os
from typing import Any, Iterator

import requests

from ._http import DEFAULT_BASE_URL, HTTPClient, RateLimitInfo, clean_params
from ._result import ResultList
from .exceptions import Py2KError
from .models import Player, PlayerSummary, Team

#: snake_case filter names -> the API's camelCase query params. Anything not
#: listed here is passed through untouched, which is what the dynamic
#: attribute filters (`three_ball_gte`) want.
_PLAYER_PARAM_ALIASES = {
    "min_rating": "minRating",
    "max_rating": "maxRating",
    "badge_tier": "badgeTier",
    "team_type": "teamType",
}


def _player_params(**filters: Any) -> dict[str, Any]:
    return clean_params(**{_PLAYER_PARAM_ALIASES.get(k, k): v for k, v in filters.items()})


class NBA2KClient:
    """Client for the NBA 2K API.

    Reads the API key from the `api_key` argument, falling back to the
    `NBA2K_API_KEY` environment variable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        auto_retry_rate_limit: bool = True,
        max_retries: int = 2,
        session: requests.Session | None = None,
    ) -> None:
        api_key = api_key or os.environ.get("NBA2K_API_KEY")
        if not api_key:
            raise Py2KError(
                "No API key provided. Pass api_key=... or set the NBA2K_API_KEY "
                "environment variable. Get a key from https://www.nba2kapi.com/dashboard"
            )
        self._http = HTTPClient(
            api_key,
            base_url=base_url,
            timeout=timeout,
            auto_retry_rate_limit=auto_retry_rate_limit,
            max_retries=max_retries,
            session=session,
        )

    @property
    def api_key(self) -> str:
        return self._http.api_key

    @property
    def rate_limit(self) -> RateLimitInfo:
        return self._http.rate_limit

    # -- players -------------------------------------------------------------

    def get_players(
        self,
        *,
        era: str | None = None,
        position: str | None = None,
        team: str | None = None,
        min_rating: int | None = None,
        max_rating: int | None = None,
        badge: str | None = None,
        badge_tier: str | None = None,
        sort: str | None = None,
        fields: str | list[str] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        **attribute_filters: int,
    ) -> ResultList[PlayerSummary]:
        """List/filter/sort/paginate players. Extra kwargs are passed through
        as-is, e.g. `three_ball_gte=85`, to support the API's 40+ dynamic
        attribute filters."""
        params = _player_params(
            era=era,
            position=position,
            team=team,
            min_rating=min_rating,
            max_rating=max_rating,
            badge=badge,
            badge_tier=badge_tier,
            sort=sort,
            fields=fields,
            limit=limit,
            cursor=cursor,
            **attribute_filters,
        )
        payload = self._http.request("GET", "/players", params=params)
        items = [PlayerSummary.model_validate(p) for p in payload.get("data", [])]
        return ResultList(items, payload.get("meta"))

    def iter_players(self, *, page_size: int = 100, **filters: Any) -> Iterator[PlayerSummary]:
        """Follow cursor pagination automatically, yielding one player at a time."""
        cursor = filters.pop("cursor", None)
        while True:
            page = self.get_players(limit=page_size, cursor=cursor, **filters)
            yield from page
            cursor = page.next_cursor
            if not cursor:
                return

    def get_players_bulk(self, **filters: Any) -> ResultList[PlayerSummary]:
        """Fetch the entire matching dataset in one call (one request against
        your rate limit), per the API's /players/bulk endpoint.

        Accepts the same filter names as `get_players`."""
        params = _player_params(**filters)
        payload = self._http.request("GET", "/players/bulk", params=params)
        items = [PlayerSummary.model_validate(p) for p in payload.get("data", [])]
        return ResultList(items, payload.get("meta"))

    def get_player(self, slug: str, *, team_type: str | None = None) -> Player:
        params = clean_params(teamType=team_type)
        payload = self._http.request("GET", f"/players/slug/{slug}", params=params)
        return Player.model_validate(payload.get("data", payload))

    def search_players(
        self, q: str, *, team_type: str | None = None, limit: int | None = None
    ) -> ResultList[PlayerSummary]:
        params = clean_params(q=q, teamType=team_type, limit=limit)
        payload = self._http.request("GET", "/players/search", params=params)
        items = [PlayerSummary.model_validate(p) for p in payload.get("data", [])]
        return ResultList(items, payload.get("meta"))

    # -- teams -----------------------------------------------------------

    def get_teams(self, *, era: str | None = None) -> ResultList[Team]:
        params = clean_params(era=era)
        payload = self._http.request("GET", "/teams", params=params)
        items = [Team.model_validate(t) for t in payload.get("data", [])]
        return ResultList(items, payload.get("meta"))

    def get_team_roster(self, team: str, *, team_type: str | None = None) -> ResultList[PlayerSummary]:
        params = clean_params(teamType=team_type)
        payload = self._http.request("GET", f"/teams/{team}/roster", params=params)
        items = [PlayerSummary.model_validate(p) for p in payload.get("data", [])]
        return ResultList(items, payload.get("meta"))

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "NBA2KClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()