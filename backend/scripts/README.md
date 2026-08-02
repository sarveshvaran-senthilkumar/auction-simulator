# Scripts

## What the app actually uses

| Script | Purpose |
|---|---|
| `build_seed_data.py` | **Generates the shipped dataset** into `backend/data/`. Run this first. |
| `smoke_auction.py` | Runs a complete AI-only auction through the engine and checks every rule invariant. No browser or server needed. |

```bash
python scripts/build_seed_data.py   # writes backend/data/*.json
python -m app.db.seed_db            # loads them into SQLite
python scripts/smoke_auction.py     # optional: verify the engine end to end
```

## Legacy ETL stubs

`scrape_auction_list.py`, `scrape_squad_2024.py`, `scrape_player_stats.py`,
`scrape_venue_stats.py` and `build_master_pool.py` are the original scraping
pipeline from the implementation plan. They are **mock stubs** that write to
`data/raw/`, which nothing reads any more.

They were replaced by `build_seed_data.py` because live scraping needs network
access, breaks whenever a source page changes, and made the app impossible to
start offline. Keep them if you want to wire up real sources later — the JSON
shapes `seed_db.py` expects are documented at the top of `build_seed_data.py`.

`calibrate_impact_weights.py` is the offline regression that produced the
weights now inlined in `build_seed_data.py` and written to `data/weights.json`.
