from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from ..db.models import RoomStatus
from .team import TeamResponse

class RoomCreate(BaseModel):
    host_display_name: str
    config: Optional[Dict[str, Any]] = None

class RoomResponse(BaseModel):
    id: UUID
    room_code: str
    status: RoomStatus
    host_user_id: Optional[UUID] = None
    config_json: Optional[Dict[str, Any]] = None
    teams: List[TeamResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
