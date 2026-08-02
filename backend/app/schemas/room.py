from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from ..db.models import RoomStatus
from .team import TeamResponse


class RoomCreate(BaseModel):
    host_display_name: str
    franchise_code: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class JoinRequest(BaseModel):
    franchise_code: str
    display_name: Optional[str] = None
    user_id: Optional[str] = None


class RoomResponse(BaseModel):
    id: str
    room_code: str
    status: RoomStatus
    host_user_id: Optional[str] = None
    joined_user_id: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    teams: List[TeamResponse] = []

    model_config = ConfigDict(from_attributes=True)
