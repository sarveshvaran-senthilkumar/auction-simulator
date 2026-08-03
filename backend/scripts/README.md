# Scripts

Four scripts, all of them real — there are no mocks or stubs here.

## Building the dataset

| Script | What it does |
| --- | --- |
| `build_seed_data.py` | Generates the player universe into `backend/data/`: the 2024 squads, the 2025 auction entrants, venues, franchises and the calibrated Impact weights. |
| `scrape_player_stats.py` | Downloads Cricsheet's ball-by-ball archive and computes **real** career stats for every player it can match — strike rate, powerplay and death splits, economy, dot-ball %, match-winning performances, and recency. Overwrites `data/player_stats.json`. |

Run them in this order, then load the result:

```bash
python scripts/build_seed_data.py        # writes data/*.json (256 players)
python scripts/scrape_player_stats.py    # replaces the stats with real ones
python -m app.db.seed_db                 # loads everything into auction.db
```

`build_seed_data.py` alone is enough to get a playable app — it produces
deterministic estimated stats. Running `scrape_player_stats.py` afterwards
upgrades 251 of the 256 players to real Cricsheet records; the five it can't
match are uncapped players with no IPL history, and they keep the estimate
(flagged `"source": "generated"` in the JSON).

Add `--refresh` to re-download the archive instead of using the cached copy in
`data/raw/` (gitignored, ~6.8 MB).

## Testing

| Script | What it checks |
| --- | --- |
| `smoke_auction.py` | Runs a complete AI-only auction through the engine and asserts every rule invariant: squad caps, overseas caps, purse floors, RTM consumption, AI squad-shape diversity. No server or browser needed. |
| `smoke_client.py` | Drives a running server over HTTP + WebSocket the way a phone does: create room, claim a franchise, confirm retentions, bid on live lots. |

```bash
python scripts/smoke_auction.py

# smoke_client needs a server on :8000
python -m uvicorn app.main:app --port 8000    # in another terminal
python scripts/smoke_client.py
```

The frontend has a matching end-to-end test — see `frontend/render_test.mjs`.
