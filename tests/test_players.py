import pytest
import responses

BASE = "https://api.nba2kapi.com/api"


@responses.activate
def test_get_players(client):
    responses.add(
        responses.GET,
        f"{BASE}/players",
        json={
            "success": True,
            "data": [
                {
                    "name": "Shai Gilgeous-Alexander",
                    "slug": "shai-gilgeous-alexander",
                    "team": "Oklahoma City Thunder",
                    "teamType": "curr",
                    "overall": 98,
                    "positions": ["PG", "SG"],
                }
            ],
            "meta": {"pagination": {"total": 231, "nextCursor": "50"}},
        },
        status=200,
    )

    players = client.get_players(position="guard", era="all", three_ball_gte=85, sort="overall:desc")

    assert len(players) == 1
    assert players[0].name == "Shai Gilgeous-Alexander"
    assert players[0].team_type == "curr"
    assert players.total == 231
    assert players.next_cursor == "50"

    request = responses.calls[0].request
    assert request.headers["X-API-Key"] == "test-key"
    assert "three_ball_gte=85" in request.url
    assert "position=guard" in request.url


@responses.activate
def test_get_player_by_slug(client):
    responses.add(
        responses.GET,
        f"{BASE}/players/slug/lebron-james",
        json={
            "success": True,
            "data": {
                "name": "LeBron James",
                "slug": "lebron-james",
                "team": "Los Angeles Lakers",
                "overall": 96,
                "attributes": {"threePointShot": 85},
                "badges": {"total": 26},
            },
        },
        status=200,
    )

    player = client.get_player("lebron-james")
    assert player.name == "LeBron James"
    assert player.attributes["threePointShot"] == 85


@responses.activate
def test_iter_players_follows_cursor(client):
    responses.add(
        responses.GET,
        f"{BASE}/players",
        json={
            "success": True,
            "data": [{"name": "Player A", "slug": "player-a"}],
            "meta": {"pagination": {"total": 2, "nextCursor": "1"}},
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE}/players",
        json={
            "success": True,
            "data": [{"name": "Player B", "slug": "player-b"}],
            "meta": {"pagination": {"total": 2, "nextCursor": None}},
        },
        status=200,
    )

    names = [p.name for p in client.iter_players(page_size=1)]
    assert names == ["Player A", "Player B"]
    assert len(responses.calls) == 2


@responses.activate
def test_get_players_bulk(client):
    responses.add(
        responses.GET,
        f"{BASE}/players/bulk",
        json={"success": True, "data": [{"name": "Player A", "slug": "player-a"}] * 3},
        status=200,
    )
    players = client.get_players_bulk(era="all", min_rating=90, three_ball_gte=85)
    assert len(players) == 3

    # snake_case filters map to the API's camelCase params, same as get_players;
    # dynamic attribute filters pass through untouched.
    url = responses.calls[0].request.url
    assert "minRating=90" in url
    assert "min_rating" not in url
    assert "three_ball_gte=85" in url


@responses.activate
def test_search_players(client):
    responses.add(
        responses.GET,
        f"{BASE}/players/search",
        json={
            "success": True,
            "data": [{"name": "LeBron James", "slug": "lebron-james", "overall": 96}],
            "meta": {"count": 1, "total": 1, "truncated": False},
        },
        status=200,
    )
    results = client.search_players("lebron")
    assert results[0].slug == "lebron-james"


def test_to_dataframe():
    pytest.importorskip("pandas")
    from py2k._result import ResultList
    from py2k.models import PlayerSummary

    items = ResultList([PlayerSummary(name="A", slug="a"), PlayerSummary(name="B", slug="b")])
    df = items.to_dataframe()
    assert list(df["name"]) == ["A", "B"]