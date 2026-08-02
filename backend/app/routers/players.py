import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..ai_service.impact_engine import impact_engine
from ..config import DATA_DIR
from ..db.database import get_db
from ..db.models import Player, PlayerStats, Squad2024Entry

router = APIRouter(prefix="/api", tags=["Players"])

STAT_FIELDS = [
    "matches", "innings", "batting_avg", "strike_rate", "powerplay_sr",
    "death_overs_sr", "boundary_pct", "bowling_avg", "economy", "wickets",
    "bowling_sr", "death_overs_economy", "dot_ball_pct", "match_winning_innings",
]


def _serialise(player: Player, stats: Optional[PlayerStats]) -> dict:
    return {
        "id": player.id,
        "name": player.name,
        "nationality": player.nationality,
        "role": player.role.value,
        "is_capped": player.is_capped,
        "base_price_lakh": player.base_price_lakh,
        "set_name": player.set_name,
        "is_overseas": player.is_overseas,
        "age": player.age,
        "is_fallback_price": player.is_fallback_price,
        "base_impact_score": round(stats.base_impact_score, 1) if stats and stats.base_impact_score else None,
    }


@router.get("/players")
async def list_players(
    q: Optional[str] = None,
    role: Optional[str] = None,
    overseas: Optional[bool] = None,
    capped: Optional[bool] = None,
    sort: str = Query("impact", pattern="^(impact|price|name)$"),
    limit: int = Query(60, le=300),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Player, PlayerStats).outerjoin(
        PlayerStats, PlayerStats.player_id == Player.id
    )

    if q:
        stmt = stmt.where(Player.name.ilike(f"%{q}%"))
    if role:
        stmt = stmt.where(Player.role == role)
    if overseas is not None:
        stmt = stmt.where(Player.is_overseas == overseas)
    if capped is not None:
        stmt = stmt.where(Player.is_capped == capped)

    if sort == "impact":
        stmt = stmt.order_by(PlayerStats.base_impact_score.desc().nullslast())
    elif sort == "price":
        stmt = stmt.order_by(Player.base_price_lakh.desc())
    else:
        stmt = stmt.order_by(Player.name)

    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()

    rows = (await db.execute(stmt.limit(limit).offset(offset))).all()
    return {
        "total": total,
        "items": [_serialise(p, s) for p, s in rows],
    }


@router.get("/players/{player_id}")
async def get_player(player_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        select(Player, PlayerStats)
        .outerjoin(PlayerStats, PlayerStats.player_id == Player.id)
        .where(Player.id == player_id)
    )).first()
    if row is None:
        raise HTTPException(404, "Player not found")

    player, stats = row
    squad = (await db.execute(
        select(Squad2024Entry).where(Squad2024Entry.player_id == player_id)
    )).scalar_one_or_none()

    impact = impact_engine.compute_impact(player, stats)
    return {
        **_serialise(player, stats),
        "franchise_2024": squad.franchise_code if squad else None,
        "stats": {f: getattr(stats, f, None) for f in STAT_FIELDS} if stats else {},
        "impact": impact.model_dump(),
    }


@router.get("/franchises")
async def franchises():
    """Names and colours for the ten sides — drives the mobile UI theming."""
    path = DATA_DIR / "franchises.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
