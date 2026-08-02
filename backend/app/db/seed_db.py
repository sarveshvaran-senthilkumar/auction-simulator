"""Loads the static JSON dataset in `backend/data/` into the database.

Safe to re-run: it drops and recreates every table.

    python -m app.db.seed_db          (from backend/, venv active)
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.ai_service.impact_engine import impact_engine  # noqa: E402
from app.config import DATA_DIR  # noqa: E402
from app.db.database import AsyncSessionLocal, Base, engine  # noqa: E402
from app.db.models import (  # noqa: E402
    PitchTendency,
    Player,
    PlayerRole,
    PlayerStats,
    RetentionSlab,
    Squad2024Entry,
    Venue,
)
from app.engine.retention_engine import RetentionSlabRules  # noqa: E402

STAT_FIELDS = [
    "matches", "innings", "batting_avg", "strike_rate", "powerplay_sr",
    "death_overs_sr", "boundary_pct", "bowling_avg", "economy", "wickets",
    "bowling_sr", "death_overs_economy", "dot_ball_pct", "match_winning_innings",
]


def load(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        raise SystemExit(
            f"missing {path}\nRun: python scripts/build_seed_data.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


async def seed() -> None:
    players_data = load("master_pool.json")
    squads_data = load("squads_2024.json")
    stats_data = load("player_stats.json")
    venues_data = load("venues.json")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        by_name: dict[str, Player] = {}
        for p in players_data:
            player = Player(
                name=p["name"],
                nationality=p["nationality"],
                role=PlayerRole(p["role"]),
                is_capped=p["is_capped"],
                base_price_lakh=p["base_price_lakh"],
                set_name=p["set_name"],
                set_order=p["set_order"],
                is_overseas=p["is_overseas"],
                age=p["age"],
                is_fallback_price=p["is_fallback_price"],
            )
            session.add(player)
            by_name[p["name"]] = player
        await session.flush()

        stats_rows = []
        for s in stats_data:
            player = by_name.get(s["player_name"])
            if not player:
                continue
            row = PlayerStats(
                player_id=player.id,
                **{f: s.get(f) for f in STAT_FIELDS},
            )
            stats_rows.append((player, row))
            session.add(row)

        # Freeze each player's intrinsic score once, so the live auction never
        # has to recompute Layer 1 mid-lot.
        for player, row in stats_rows:
            row.base_impact_score = impact_engine.base_score(player, row)

        for s in squads_data:
            player = by_name.get(s["player_name"])
            if not player:
                continue
            session.add(Squad2024Entry(
                franchise_code=s["franchise"],
                player_id=player.id,
                role=PlayerRole(s["role"]),
                was_capped=s["was_capped"],
            ))

        for v in venues_data:
            session.add(Venue(
                franchise_code=v["franchise_code"],
                ground_name=v["ground_name"],
                avg_first_innings_score=v["avg_first_innings_score"],
                chase_success_pct=v["chase_success_pct"],
                pitch_tendency=PitchTendency(v["pitch_tendency"]),
                boundary_size_category=v["boundary_size_category"],
                source_url=v.get("source_url"),
            ))

        for slot, costs in RetentionSlabRules.SLABS.items():
            session.add(RetentionSlab(
                slot_no=slot,
                capped_cost_lakh=costs["capped"],
                uncapped_cost_lakh=costs["uncapped"],
            ))

        await session.commit()

    print(f"seeded {len(players_data)} players")
    print(f"seeded {len(squads_data)} 2024 squad entries")
    print(f"seeded {len(venues_data)} venues + {len(RetentionSlabRules.SLABS)} retention slabs")


async def report_top() -> None:
    """Sanity check from the plan: the top of the board should look sane."""
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            select(Player, PlayerStats)
            .join(PlayerStats, PlayerStats.player_id == Player.id)
            .order_by(PlayerStats.base_impact_score.desc())
            .limit(10)
        )
        print("\nTop 10 by Impact Score:")
        for player, stats in rows.all():
            print(f"  {stats.base_impact_score:5.1f}  {player.name:24s} {player.role.value}")


if __name__ == "__main__":
    asyncio.run(seed())
    asyncio.run(report_top())
