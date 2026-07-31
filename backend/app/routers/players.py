from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..db.database import get_db
from ..db.models import Player
from ..schemas.player import PlayerResponse

router = APIRouter(prefix="/api/players", tags=["Players"])

@router.get("/", response_model=List[PlayerResponse])
async def get_players(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).limit(100))
    players = result.scalars().all()
    return players

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
