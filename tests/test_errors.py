import pytest
import responses

from py2k import AuthenticationError, NBA2KClient, NotFoundError, Py2KError, RateLimitError

BASE = "https://api.nba2kapi.com/api"


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("NBA2K_API_KEY", raising=False)
    with pytest.raises(Py2KError):
        NBA2KClient()


def test_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("NBA2K_API_KEY", "from-env")
    client = NBA2KClient()
    assert client.api_key == "from-env"


@responses.activate
def test_authentication_error(client):
    responses.add(
        responses.GET,
        f"{BASE}/players",
        json={"success": False, "error": {"message": "Invalid API key", "code": "UNAUTHORIZED"}},
        status=401,
    )
    with pytest.raises(AuthenticationError):
        client.get_players()


@responses.activate
def test_not_found_error(client):
    responses.add(
        responses.GET,
        f"{BASE}/players/slug/nobody",
        json={"success": False, "error": {"message": "Player not found", "code": "NOT_FOUND"}},
        status=404,
    )
    with pytest.raises(NotFoundError):
        client.get_player("nobody")


@responses.activate
def test_rate_limit_retries_then_succeeds(client, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    responses.add(
        responses.GET,
        f"{BASE}/players",
        json={
            "success": False,
            "error": {
                "message": "You have exceeded your rate limit",
                "code": "RATE_LIMIT_EXCEEDED",
                "details": {"limit": 500, "retryAfter": 1},
            },
        },
        status=429,
    )
    responses.add(
        responses.GET,
        f"{BASE}/players",
        json={"success": True, "data": [{"name": "Player A", "slug": "player-a"}]},
        status=200,
    )

    players = client.get_players()
    assert players[0].name == "Player A"
    assert len(responses.calls) == 2


@responses.activate
def test_rate_limit_raises_after_max_retries():
    client = NBA2KClient(api_key="test-key", max_retries=0)
    responses.add(
        responses.GET,
        f"{BASE}/players",
        json={
            "success": False,
            "error": {
                "message": "You have exceeded your rate limit",
                "code": "RATE_LIMIT_EXCEEDED",
                "details": {"retryAfter": 1},
            },
        },
        status=429,
    )
    with pytest.raises(RateLimitError) as exc_info:
        client.get_players()
    assert exc_info.value.retry_after == 1