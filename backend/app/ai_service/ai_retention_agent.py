import random
from typing import List, Dict

class AIRetentionAgent:
    def decide_retentions(self, squad_2024: List[Dict], impact_scores: Dict[str, float]) -> List[Dict]:
        """
        Decides which players to retain for an AI team based on Impact Scores.
        Returns a list of selected players and their assigned slots.
        """
        # Sort squad by impact score descending
        sorted_squad = sorted(
            squad_2024, 
            key=lambda p: impact_scores.get(str(p['player_id']), 0), 
            reverse=True
        )
        
        retained = []
        capped_retained = 0
        uncapped_retained = 0
        
        # Determine how aggressive this AI should be (retain 3-6 players)
        target_retentions = random.randint(3, 6)
        
        for player in sorted_squad:
            if len(retained) >= target_retentions:
                break
                
            if player['is_capped']:
                if capped_retained < 5:
                    capped_retained += 1
                    retained.append({
                        "player_id": player['player_id'],
                        "is_capped": True,
                        "slot_no": capped_retained # Assign slots 1 to 5
                    })
            else:
                if uncapped_retained < 2:
                    uncapped_retained += 1
                    retained.append({
                        "player_id": player['player_id'],
                        "is_capped": False,
                        "slot_no": 0
                    })
                    
        return retained

ai_retention_agent = AIRetentionAgent()
