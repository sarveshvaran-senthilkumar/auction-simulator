"""AI retention strategy: value-ranked, role-aware, with per-team appetite."""

import random
from typing import Dict, List

from ..engine.retention_engine import RetentionSlabRules, retention_engine
from .impact_engine import StatsView, impact_engine


class AIRetentionAgent:
    def decide_retentions(self, team, squad: List, venue=None) -> List[Dict]:
        """`squad` is a list of PlayerRef for this franchise's 2024 side.

        Returns picks in the order they should occupy retention slots.
        """
        need = team.need()
        scored = []
        for player in squad:
            impact = impact_engine.compute_impact(player, StatsView(player), need, venue)
            scored.append((impact.suggested_value_lakh, impact.base_score, player))
        scored.sort(key=lambda row: row[0], reverse=True)

        # Not every franchise maxes out -- some keep powder dry for the auction.
        target = random.choices([3, 4, 5, 6], weights=[0.2, 0.3, 0.3, 0.2])[0]

        picks: List[Dict] = []
        capped_taken = 0
        uncapped_taken = 0
        role_taken: Dict[str, int] = {}
        purse = team.purse_remaining_lakh

        for market_value, _base, player in scored:
            if len(picks) >= target:
                break

            is_capped = player.is_capped
            if is_capped and capped_taken >= RetentionSlabRules.MAX_CAPPED:
                continue
            if not is_capped and uncapped_taken >= RetentionSlabRules.MAX_UNCAPPED:
                continue

            cost = retention_engine.cost_for(
                capped_taken + 1 if is_capped else 0, is_capped
            )
            if cost > purse:
                continue

            # Don't stockpile one role -- three of anything is plenty to retain.
            if role_taken.get(player.role, 0) >= 3:
                continue

            # Only retain when the slab price is a fair deal against market value.
            # Uncapped players at a flat 4cr are a bargain whenever they're good.
            threshold = 0.75 if is_capped else 0.55
            if market_value < cost * threshold:
                continue

            picks.append({"player_id": player.id, "is_capped": is_capped})
            purse -= cost
            role_taken[player.role] = role_taken.get(player.role, 0) + 1
            if is_capped:
                capped_taken += 1
            else:
                uncapped_taken += 1

        return picks


ai_retention_agent = AIRetentionAgent()
