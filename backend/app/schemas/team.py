from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID

class TeamBase(BaseModel):
    franchise_code: str
    is_ai: bool

class TeamResponse(TeamBase):
    id: UUID
    room_id: UUID
    user_id: Optional[UUID] = None
    purse_remaining_lakh: int
    overseas_slots_used: int
    
    model_config = ConfigDict(from_attributes=True)
