from typing import Optional

from pydantic import BaseModel, ConfigDict


class TeamResponse(BaseModel):
    id: str
    room_id: str
    franchise_code: str
    user_id: Optional[str] = None
    is_ai: bool
    purse_remaining_lakh: int
    overseas_slots_used: int = 0
    retention_confirmed: bool = False

    model_config = ConfigDict(from_attributes=True)
