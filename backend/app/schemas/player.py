from typing import Optional

from pydantic import BaseModel, ConfigDict

from ..db.models import PlayerRole


class PlayerResponse(BaseModel):
    id: str
    name: str
    nationality: str
    role: PlayerRole
    is_capped: bool
    base_price_lakh: int
    set_name: Optional[str] = None
    is_overseas: bool
    age: Optional[int] = None
    is_fallback_price: bool = False
    base_impact_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
