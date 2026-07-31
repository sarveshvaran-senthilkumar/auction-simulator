from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from ..db.models import PlayerRole

class PlayerBase(BaseModel):
    name: str
    nationality: str
    role: PlayerRole
    is_capped: bool
    base_price_lakh: int
    set_name: Optional[str] = None
    is_overseas: bool
    age: Optional[int] = None

class PlayerResponse(PlayerBase):
    id: UUID
    is_fallback_price: bool
    
    model_config = ConfigDict(from_attributes=True)
