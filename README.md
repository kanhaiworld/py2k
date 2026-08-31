# py2k

Unofficial Python client for the [NBA 2K API](https://www.nba2kapi.com) — player ratings, attributes, badges, and team rosters across the current, classic, and all-time NBA 2K player pool.

```python
from py2k import NBA2KClient

client = NBA2KClient()  # reads NBA2K_API_KEY from the environment

# Filter, sort, paginate
guards = client.get_players(position="guard", min_rating=90, sort="overall:desc")
for p in guards:
    print(p.name, p.overall)

# Dynamic attribute filters (any of the API's 40+ attributes)
shooters = client.get_players(three_ball_gte=85)

# Full player detail
lebron = client.get_player("lebron-james")
print(lebron.attributes)

# Search
matches = client.search_players("lebron")

# Teams and rosters
teams = client.get_teams(era="curr")
lakers = client.get_team_roster("los-angeles-lakers")

# Walk the entire filtered result set, following pagination automatically
for p in client.iter_players(position="center"):
    ...

# Or grab everything matching a filter in one call (counts once against your rate limit)
all_centers = client.get_players_bulk(position="center")
```

## Installation

Requires Python 3.10+.

Not yet published to PyPI. Once it is, it'll be `pip install pynba2k` (the
distribution name is `pynba2k`; you still `import py2k` in code).

For now, install from source:

```bash
pip install -e ".[dev]"   # local development
```

Or, using the pinned requirements files:

```bash
pip install -r requirements-dev.txt   # runtime + dev/test deps
pip install -e . --no-deps            # install py2k itself, editable
```

## Authentication

Get a key from the [nba2kapi.com dashboard](https://www.nba2kapi.com/dashboard) and either pass it directly or set it as an environment variable:

```bash
export NBA2K_API_KEY=your-key-here
```

```python
client = NBA2KClient(api_key="your-key-here")
```

## Rate limits

The free tier allows 500 requests/hour. The client reads `X-RateLimit-*` response headers into `client.rate_limit` after every call, and automatically retries once on `429` responses using the API's `retryAfter` value (configurable via `auto_retry_rate_limit` / `max_retries`).

## pandas integration

Any result list supports `.to_dataframe()`:

```bash
pip install "pynba2k[dataframe]"
```

```python
df = client.get_players(era="all").to_dataframe()
```

## Status

Early scaffold — core endpoints (`players`, `players/bulk`, `players/slug/:slug`, `players/search`, `teams`, `teams/:team/roster`) are wrapped, but models are permissive (`extra="allow"`) since exact field schemas haven't been verified against a live API key yet. Expect field names/types to tighten up once we've run this against real responses.

## Running tests

```bash
pytest
```
