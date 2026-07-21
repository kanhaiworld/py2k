import responses

BASE = "https://api.nba2kapi.com/api"


@responses.activate
def test_get_teams(client):
    responses.add(
        responses.GET,
        f"{BASE}/teams",
        json={
            "success": True,
            "data": [
                {"teamName": "Los Angeles Lakers", "teamType": "curr", "playerCount": 17, "averageRating": 82.4}
            ],
        },
        status=200,
    )
    teams = client.get_teams(era="curr")
    assert teams[0].team_name == "Los Angeles Lakers"
    assert teams[0].average_rating == 82.4


@responses.activate
def test_get_team_roster(client):
    responses.add(
        responses.GET,
        f"{BASE}/teams/los-angeles-lakers/roster",
        json={"success": True, "data": [{"name": "LeBron James", "slug": "lebron-james"}]},
        status=200,
    )
    roster = client.get_team_roster("los-angeles-lakers")
    assert roster[0].slug == "lebron-james"