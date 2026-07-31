import random
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..db.database import get_db
from ..db.models import Room, Team, User, RoomStatus
from ..schemas.room import RoomCreate, RoomResponse
from ..config import settings

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@router.post("/", response_model=RoomResponse)
async def create_room(req: RoomCreate, db: AsyncSession = Depends(get_db)):
    # 1. Create User
    host = User(display_name=req.host_display_name)
    db.add(host)
    await db.flush()
    
    # 2. Create Room
    room = Room(
        room_code=generate_room_code(),
        host_user_id=host.id,
        config_json=req.config or {}
    )
    db.add(room)
    await db.flush()
    
    # 3. Create Teams
    franchises = ["CSK", "MI", "RCB", "KKR", "DC", "RR", "PBKS", "SRH", "LSG", "GT"]
    for code in franchises:
        team = Team(
            room_id=room.id,
            franchise_code=code,
            purse_remaining_lakh=settings.DEFAULT_PURSE_LAKH,
            is_ai=True
        )
        db.add(team)
        
    await db.commit()
    
    # Return re-fetched room with teams
    result = await db.execute(
        select(Room).where(Room.id == room.id)
    )
    # We would join teams normally, simplified for mock
    return room
