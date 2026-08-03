import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..auth.security import current_user_optional
from ..config import settings
from ..db.database import get_db
from ..db.models import Room, RoomStatus, Team, User
from ..engine.auction_engine import auction_engine
from ..schemas.room import JoinRequest, RoomCreate, RoomResponse
from ..schemas.team import TeamResponse

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])

FRANCHISES = ["CSK", "MI", "RCB", "KKR", "DC", "RR", "PBKS", "SRH", "LSG", "GT"]

# Avoid characters that are easy to misread when someone reads a code aloud.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


async def _unique_code(db: AsyncSession) -> str:
    for _ in range(20):
        code = "".join(random.choices(CODE_ALPHABET, k=6))
        exists = (await db.execute(
            select(Room).where(Room.room_code == code)
        )).scalar_one_or_none()
        if exists is None:
            return code
    raise HTTPException(500, "Could not allocate a room code")


def _room_payload(room: Room, teams: list[Team]) -> dict:
    return {
        "id": room.id,
        "room_code": room.room_code,
        "status": room.status,
        "host_user_id": room.host_user_id,
        "config_json": room.config_json,
        "teams": [TeamResponse.model_validate(t) for t in teams],
    }


@router.post("", response_model=RoomResponse)
@router.post("/", response_model=RoomResponse, include_in_schema=False)
async def create_room(
    req: RoomCreate,
    db: AsyncSession = Depends(get_db),
    account: Optional[User] = Depends(current_user_optional),
):
    # A signed-in host keeps their account (and their name in the lobby);
    # anyone else gets a throwaway user so the room still works.
    if account is not None:
        host = account
    else:
        host = User(display_name=req.host_display_name or "Manager")
        db.add(host)
        await db.flush()

    room = Room(
        room_code=await _unique_code(db),
        host_user_id=host.id,
        config_json=req.config or {},
        status=RoomStatus.LOBBY,
    )
    db.add(room)
    await db.flush()

    teams = []
    for code in FRANCHISES:
        team = Team(
            room_id=room.id,
            franchise_code=code,
            purse_remaining_lakh=settings.DEFAULT_PURSE_LAKH,
            is_ai=True,
        )
        db.add(team)
        teams.append(team)

    # The host takes a franchise straight away, so a solo player can go from
    # "Create" to the retention screen without a separate join step.
    if req.franchise_code:
        picked = next((t for t in teams if t.franchise_code == req.franchise_code), None)
        if picked is None:
            raise HTTPException(400, "Unknown franchise")
        picked.user_id = host.id
        picked.is_ai = False

    await db.commit()
    payload = _room_payload(room, teams)
    payload["host_user_id"] = host.id
    return payload


@router.get("/{code}", response_model=RoomResponse)
async def get_room(code: str, db: AsyncSession = Depends(get_db)):
    code = code.upper()
    room = (await db.execute(
        select(Room).where(Room.room_code == code)
    )).scalar_one_or_none()
    if room is None:
        raise HTTPException(404, "Room not found")
    teams = (await db.execute(select(Team).where(Team.room_id == room.id))).scalars().all()
    return _room_payload(room, teams)


@router.post("/{code}/join", response_model=RoomResponse)
async def join_room(
    code: str,
    req: JoinRequest,
    db: AsyncSession = Depends(get_db),
    account: Optional[User] = Depends(current_user_optional),
):
    code = code.upper()
    room = (await db.execute(
        select(Room).where(Room.room_code == code)
    )).scalar_one_or_none()
    if room is None:
        raise HTTPException(404, "Room not found")
    if room.status != RoomStatus.LOBBY:
        raise HTTPException(409, "This auction has already started")

    teams = (await db.execute(select(Team).where(Team.room_id == room.id))).scalars().all()
    target = next((t for t in teams if t.franchise_code == req.franchise_code), None)
    if target is None:
        raise HTTPException(400, "Unknown franchise")
    if not target.is_ai:
        raise HTTPException(409, "That franchise is already taken")

    user = account
    if user is None and req.user_id:
        user = (await db.execute(
            select(User).where(User.id == req.user_id)
        )).scalar_one_or_none()
    if user is None:
        user = User(display_name=req.display_name or "Manager")
        db.add(user)
        await db.flush()

    # One franchise per person: release whatever they held before.
    for t in teams:
        if t.user_id == user.id:
            t.user_id = None
            t.is_ai = True

    target.user_id = user.id
    target.is_ai = False
    await db.commit()

    payload = _room_payload(room, teams)
    payload["joined_user_id"] = user.id
    return payload


@router.post("/{code}/start", response_model=RoomResponse)
async def start_retention(code: str, db: AsyncSession = Depends(get_db)):
    code = code.upper()
    room = (await db.execute(
        select(Room).where(Room.room_code == code)
    )).scalar_one_or_none()
    if room is None:
        raise HTTPException(404, "Room not found")

    state = await auction_engine.start_retention(code)

    teams = (await db.execute(select(Team).where(Team.room_id == room.id))).scalars().all()
    payload = _room_payload(room, teams)
    payload["status"] = RoomStatus(state.status)
    return payload


@router.get("/{code}/state")
async def room_state(code: str):
    """Live in-memory state — the WebSocket sends the same shape."""
    code = code.upper()
    state = auction_engine.get(code)
    if state is None:
        state = await auction_engine.load_room(code)
    return state.public()


@router.get("/{code}/retention-pool/{team_id}")
async def retention_pool(code: str, team_id: str):
    """The team's 2024 squad with impact scores, for the retention screen."""
    from ..ai_service.impact_engine import StatsView, impact_engine

    code = code.upper()
    room = auction_engine.get(code) or await auction_engine.load_room(code)
    team = room.teams.get(team_id)
    if team is None:
        raise HTTPException(404, "Team not found")

    venue = auction_engine.venue_for(room, team)
    squad = auction_engine.squad_2024_of(room, team)

    players = []
    for player in squad:
        impact = impact_engine.compute_impact(player, StatsView(player), team.need(), venue)
        players.append({
            **player.public(),
            "impact": impact.model_dump(),
        })

    return {
        "team": team.public(),
        "venue": {
            "ground_name": venue.ground_name,
            "pitch_tendency": venue.pitch_tendency.value if venue.pitch_tendency else None,
        } if venue else None,
        "players": players,
        "purse_lakh": team.purse_remaining_lakh,
    }


@router.get("/{code}/unsold")
async def unsold(code: str):
    """Players who went unsold, and whether they come back around."""
    code = code.upper()
    room = auction_engine.get(code)
    if room is None:
        raise HTTPException(404, "Room not loaded")
    players = room.unsold_players()
    return {
        "total": len(players),
        "returning": sum(1 for p in players if p["returns"]),
        "players": players,
    }


@router.get("/{code}/results")
async def results(code: str):
    code = code.upper()
    room = auction_engine.get(code)
    if room is None:
        raise HTTPException(404, "Room not loaded")
    return auction_engine.results(room)
