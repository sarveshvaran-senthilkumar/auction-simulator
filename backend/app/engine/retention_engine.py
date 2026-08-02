"""Retention slab rules and validation, mirroring the real 2025 mega auction."""

from typing import Dict, List, Tuple


class RetentionSlabRules:
    # Capped retentions are priced by slot; uncapped is a flat 4 crore.
    SLABS = {
        1: {"capped": 1800, "uncapped": 400},
        2: {"capped": 1400, "uncapped": 400},
        3: {"capped": 1100, "uncapped": 400},
        4: {"capped": 1800, "uncapped": 400},
        5: {"capped": 1400, "uncapped": 400},
    }
    UNCAPPED_COST = 400
    MAX_CAPPED = 5
    MAX_UNCAPPED = 2
    MAX_TOTAL = 6


class RetentionEngine:
    def cost_for(self, index_among_capped: int, is_capped: bool) -> int:
        """Cost of the Nth retention. `index_among_capped` is 1-based."""
        if not is_capped:
            return RetentionSlabRules.UNCAPPED_COST
        slab = RetentionSlabRules.SLABS.get(index_among_capped)
        if slab is None:
            raise ValueError(f"no retention slab for slot {index_among_capped}")
        return slab["capped"]

    def assign_slots(self, picks: List[Dict]) -> List[Dict]:
        """Assign slab slots in pick order and attach each retention's cost.

        Capped players take slots 1..5 in the order the user selected them, so
        the first capped pick always costs 18cr. Uncapped picks get slot None.
        """
        capped_seen = 0
        priced = []
        for pick in picks:
            is_capped = bool(pick.get("is_capped"))
            if is_capped:
                capped_seen += 1
                slot = capped_seen
            else:
                slot = None
            priced.append({
                **pick,
                "slot_no": slot,
                "retention_cost_lakh": self.cost_for(capped_seen if is_capped else 0, is_capped),
                "is_uncapped": not is_capped,
            })
        return priced

    def validate(self, picks: List[Dict], purse_lakh: int) -> Tuple[bool, str]:
        if len(picks) > RetentionSlabRules.MAX_TOTAL:
            return False, f"Maximum {RetentionSlabRules.MAX_TOTAL} retentions"

        player_ids = [p["player_id"] for p in picks]
        if len(set(player_ids)) != len(player_ids):
            return False, "Duplicate player in retention list"

        capped = sum(1 for p in picks if p.get("is_capped"))
        uncapped = len(picks) - capped

        if capped > RetentionSlabRules.MAX_CAPPED:
            return False, f"Maximum {RetentionSlabRules.MAX_CAPPED} capped retentions"
        if uncapped > RetentionSlabRules.MAX_UNCAPPED:
            return False, f"Maximum {RetentionSlabRules.MAX_UNCAPPED} uncapped retentions"

        total = self.total_cost(picks)
        if total > purse_lakh:
            return False, "Retentions exceed your purse"

        return True, ""

    def total_cost(self, picks: List[Dict]) -> int:
        return sum(p["retention_cost_lakh"] for p in self.assign_slots(picks))

    def calculate_rtm_cards(self, num_retained: int) -> int:
        return max(0, RetentionSlabRules.MAX_TOTAL - num_retained)


retention_engine = RetentionEngine()
