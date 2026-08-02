"""Three-layer player valuation.

    Layer 1  base_score     intrinsic ability, role-weighted, 0-100. Frozen at seed time.
    Layer 2  context_score  what this player is worth *to this team* right now.
    Layer 3  auction value  base + context -> a rupee ceiling for the current lot.

Every component is returned in `breakdown` so the app can show "why this score".
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from ..config import DATA_DIR


class ImpactResult(BaseModel):
    base_score: float
    context_score: float
    suggested_value_lakh: int
    breakdown: Dict[str, float]
    notes: List[str] = []


class StatsView:
    """Adapts a cached PlayerRef's stat dict to the attribute access the engine wants.

    Live auction code works from denormalised PlayerRef objects rather than the
    ORM rows, so this lets one scoring path serve both.
    """

    def __init__(self, player: Any) -> None:
        self._stats = getattr(player, "stats", None) or {}
        self.base_impact_score = getattr(player, "base_impact_score", None)

    def __getattr__(self, name: str) -> Any:
        return self._stats.get(name)


@dataclass
class TeamNeed:
    """The slice of team state Layer 2 cares about."""
    purse_remaining_lakh: int = 12000
    squad_size: int = 0
    max_squad_size: int = 25
    overseas_used: int = 0
    max_overseas: int = 8
    role_counts: Dict[str, int] = field(default_factory=dict)
    franchise_code: Optional[str] = None
    aggression: float = 1.0


# A balanced XI-and-bench shape; Layer 2 scores scarcity against this.
TARGET_ROLE_MIX = {
    "Batter": 6,
    "Bowler": 7,
    "All-Rounder": 5,
    "Wicket-Keeper": 2,
}

# Stats where a lower number is better, so the 0-1 normalisation flips.
INVERTED = {"bowling_avg", "economy", "bowling_sr", "death_overs_economy"}

# Observed IPL ranges used to normalise each stat to 0-1.
STAT_RANGE = {
    "batting_avg": (12.0, 46.0),
    "strike_rate": (105.0, 172.0),
    "powerplay_sr": (95.0, 175.0),
    "death_overs_sr": (120.0, 210.0),
    "boundary_pct": (34.0, 66.0),
    "bowling_avg": (18.0, 42.0),
    "economy": (6.6, 10.8),
    "bowling_sr": (13.0, 32.0),
    "death_overs_economy": (7.5, 13.0),
    "dot_ball_pct": (22.0, 48.0),
    "wickets": (0.0, 180.0),
    "match_winning_innings": (0.0, 30.0),
}

PITCH_FIT = {
    # (pitch tendency, role) -> multiplier applied to the venue-fit component
    ("SPIN_FRIENDLY", "Bowler"): 1.15,
    ("SPIN_FRIENDLY", "All-Rounder"): 1.08,
    ("SPIN_FRIENDLY", "Batter"): 0.95,
    ("PACE_FRIENDLY", "Bowler"): 1.12,
    ("BATTING_FRIENDLY", "Batter"): 1.12,
    ("BATTING_FRIENDLY", "Wicket-Keeper"): 1.10,
    ("BATTING_FRIENDLY", "Bowler"): 0.94,
}


def _norm(field_name: str, value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    low, high = STAT_RANGE.get(field_name, (0.0, 100.0))
    if high == low:
        return 0.5
    t = (value - low) / (high - low)
    t = max(0.0, min(1.0, t))
    return 1.0 - t if field_name in INVERTED else t


def _role_value(role: Any) -> str:
    return role.value if hasattr(role, "value") else str(role)


class ImpactEngine:
    def __init__(self) -> None:
        blob = self._load_weights()
        self.weights: Dict[str, Dict[str, float]] = blob.get("roles", {})
        self.value_curve: List[List[float]] = blob.get("value_curve", [[0, 20], [100, 2700]])

    def _load_weights(self) -> Dict[str, Any]:
        path = DATA_DIR / "weights.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    # ------------------------------------------------------------------ Layer 1
    def base_score(self, player: Any, stats: Any) -> float:
        """Intrinsic 0-100 ability score from calibrated role weights."""
        role = _role_value(player.role)
        weights = self.weights.get(role, {})
        if not weights or stats is None:
            return 45.0

        total_weight = 0.0
        accumulated = 0.0

        for stat_name, weight in weights.items():
            if stat_name == "experience":
                matches = getattr(stats, "matches", 0) or 0
                score = min(1.0, matches / 110.0)
            elif stat_name == "recency":
                # No season splits in the shipped dataset; age proxies for how
                # much of the career record is still current form.
                age = getattr(player, "age", None) or 28
                score = 1.0 if age <= 27 else max(0.35, 1.0 - (age - 27) * 0.06)
            else:
                score = _norm(stat_name, getattr(stats, stat_name, None))

            if score is None:
                continue  # missing data: drop the term rather than scoring it zero
            accumulated += score * weight
            total_weight += weight

        if total_weight == 0:
            return 45.0

        raw = accumulated / total_weight
        # Uncapped players carry more downside risk than their raw numbers imply.
        if not getattr(player, "is_capped", True):
            raw *= 0.93

        return round(max(0.0, min(100.0, raw * 100.0)), 2)

    # ------------------------------------------------------------------ Layer 2
    def context_score(
        self, player: Any, need: TeamNeed, venue: Any = None
    ) -> tuple[float, Dict[str, float], List[str]]:
        role = _role_value(player.role)
        notes: List[str] = []

        # Role scarcity: how far below the target shape is this team for this role?
        have = need.role_counts.get(role, 0)
        target = TARGET_ROLE_MIX.get(role, 4)
        gap = max(0.0, (target - have) / target)
        scarcity = 0.45 + gap * 0.55
        if gap > 0.6:
            notes.append(f"Thin at {role} ({have}/{target})")

        # Overseas pressure: the last few overseas slots must be spent well.
        if getattr(player, "is_overseas", False):
            remaining = max(0, need.max_overseas - need.overseas_used)
            overseas = 0.15 if remaining == 0 else min(1.0, 0.55 + remaining * 0.09)
            if remaining <= 2 and remaining > 0:
                notes.append(f"Only {remaining} overseas slot(s) left")
            elif remaining == 0:
                notes.append("Overseas quota full")
        else:
            overseas = 0.85

        # Venue fit.
        fit = 0.7
        if venue is not None and getattr(venue, "pitch_tendency", None) is not None:
            tendency = _role_value(venue.pitch_tendency)
            fit = min(1.0, 0.7 * PITCH_FIT.get((tendency, role), 1.0))
            if PITCH_FIT.get((tendency, role), 1.0) > 1.05:
                notes.append(f"Suits {venue.ground_name.split(',')[0]}")

        # Longevity: a mega auction buys three seasons, not one.
        age = getattr(player, "age", None) or 28
        longevity = 1.0 if age <= 26 else max(0.4, 1.0 - (age - 26) * 0.055)

        # Budget headroom relative to slots still to fill.
        slots_left = max(1, need.max_squad_size - need.squad_size)
        headroom = min(1.0, (need.purse_remaining_lakh / slots_left) / 600.0)

        breakdown = {
            "role_scarcity": round(scarcity, 3),
            "overseas_balance": round(overseas, 3),
            "venue_fit": round(fit, 3),
            "longevity": round(longevity, 3),
            "budget_headroom": round(headroom, 3),
        }

        score = (
            scarcity * 0.34
            + overseas * 0.18
            + fit * 0.20
            + longevity * 0.16
            + headroom * 0.12
        ) * 100.0
        return round(score, 2), breakdown, notes

    # ------------------------------------------------------------------ Layer 3
    def _curve(self, score: float) -> int:
        """Piecewise-linear map from a 0-100 blended score to a price in lakh."""
        pts = self.value_curve
        if score <= pts[0][0]:
            return int(pts[0][1])
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if score <= x1:
                t = (score - x0) / (x1 - x0) if x1 != x0 else 0.0
                return int(y0 + (y1 - y0) * t)
        return int(pts[-1][1])

    def compute_impact(
        self,
        player: Any,
        stats: Any = None,
        need: Optional[TeamNeed] = None,
        venue: Any = None,
    ) -> ImpactResult:
        need = need or TeamNeed()

        cached = getattr(stats, "base_impact_score", None) if stats is not None else None
        base = cached if cached is not None else self.base_score(player, stats)

        ctx, ctx_breakdown, notes = self.context_score(player, need, venue)

        # Base ability dominates; context tilts the number by roughly +/-20%.
        blended = base * (0.80 + 0.40 * (ctx / 100.0))
        blended = max(0.0, min(100.0, blended))

        value = self._curve(blended)
        value = max(value, player.base_price_lakh)
        value = int(value * need.aggression)

        breakdown = {
            "base_performance": base,
            "context_total": ctx,
            "blended_score": round(blended, 2),
            **ctx_breakdown,
        }

        return ImpactResult(
            base_score=round(base, 2),
            context_score=ctx,
            suggested_value_lakh=value,
            breakdown=breakdown,
            notes=notes,
        )


impact_engine = ImpactEngine()
