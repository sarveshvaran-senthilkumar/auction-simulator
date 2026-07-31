from typing import List, Dict
from uuid import UUID

class RetentionSlabRules:
    SLABS = {
        1: {"capped": 1800, "uncapped": 400},
        2: {"capped": 1400, "uncapped": 400},
        3: {"capped": 1100, "uncapped": 400},
        4: {"capped": 1800, "uncapped": 400},
        5: {"capped": 1400, "uncapped": 400},
    }
    MAX_CAPPED = 5
    MAX_UNCAPPED = 2
    MAX_TOTAL = 6

class RetentionEngine:
    def __init__(self):
        pass

    def validate_retention_picks(self, picks: List[Dict]) -> bool:
        """
        Validates if a team's retention picks are valid according to rules.
        picks: list of dicts with 'is_capped' and 'slot_no'
        """
        if len(picks) > RetentionSlabRules.MAX_TOTAL:
            return False
            
        capped_count = sum(1 for p in picks if p['is_capped'])
        uncapped_count = sum(1 for p in picks if not p['is_capped'])
        
        if capped_count > RetentionSlabRules.MAX_CAPPED:
            return False
            
        if uncapped_count > RetentionSlabRules.MAX_UNCAPPED:
            return False
            
        slots = set(p['slot_no'] for p in picks if p['is_capped'])
        if len(slots) != capped_count:
            return False # Duplicate slots or invalid slot assignment
            
        return True

    def calculate_purse_deduction(self, picks: List[Dict]) -> int:
        deduction = 0
        for p in picks:
            if p['is_capped']:
                deduction += RetentionSlabRules.SLABS[p['slot_no']]["capped"]
            else:
                deduction += RetentionSlabRules.SLABS[1]["uncapped"] # uncapped always 400
        return deduction

    def calculate_rtm_cards(self, num_retained: int) -> int:
        return max(0, RetentionSlabRules.MAX_TOTAL - num_retained)

retention_engine = RetentionEngine()
