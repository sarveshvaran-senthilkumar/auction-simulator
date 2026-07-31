import json
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Any

class ImpactResult(BaseModel):
    base_score: float
    context_score: float
    suggested_value_lakh: int
    breakdown: Dict[str, float]

class ImpactEngine:
    def __init__(self):
        self.weights = self._load_weights()
        
    def _load_weights(self) -> Dict[str, Any]:
        weights_path = Path(__file__).parent.parent.parent / "data" / "weights.json"
        if weights_path.exists():
            with open(weights_path, "r") as f:
                return json.load(f)
        return {}

    def compute_impact(self, player: Any, stats: Any, team_state: Any, venue: Any) -> ImpactResult:
        # Mock logic based on loaded weights
        role_weights = self.weights.get(player.role.value if hasattr(player.role, 'value') else str(player.role), {})
        
        # Calculate base score (0-100) using stats and weights
        # (This is a simplified mock)
        base_score = 0.0
        if stats and getattr(stats, "base_impact_score", None):
            base_score = stats.base_impact_score
        else:
            base_score = 50.0  # fallback
            
        # Context score
        context_score = 50.0
        if venue and venue.pitch_tendency:
            if player.role == "Bowler" and venue.pitch_tendency == "SPIN_FRIENDLY":
                context_score += 10.0
                
        # Scarcity / Need
        # Assume team_state dictates need
        
        # Suggested Value
        suggested_value = int(base_score * 5) + player.base_price_lakh
        
        return ImpactResult(
            base_score=round(base_score, 2),
            context_score=round(context_score, 2),
            suggested_value_lakh=suggested_value,
            breakdown={
                "Base Performance": base_score,
                "Venue Fit": context_score,
                "Role Need": 1.0,
            }
        )

impact_engine = ImpactEngine()
