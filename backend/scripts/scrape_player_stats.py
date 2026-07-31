import json
import os
from pathlib import Path

def run_scrape():
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock data output representing Statsguru + Cricsheet data
    stats = [
        {
            "player_name": "Rishabh Pant",
            "matches": 111,
            "innings": 110,
            "batting_avg": 35.31,
            "strike_rate": 148.93,
            "powerplay_sr": 130.0,
            "death_overs_sr": 180.5,
            "boundary_pct": 65.2,
            "bowling_avg": None,
            "economy": None,
            "wickets": None,
            "bowling_sr": None,
            "death_overs_economy": None,
            "dot_ball_pct": None,
            "match_winning_innings": 12,
            "base_impact_score": 88.5
        },
        {
            "player_name": "Jos Buttler",
            "matches": 107,
            "innings": 106,
            "batting_avg": 38.35,
            "strike_rate": 147.53,
            "powerplay_sr": 140.2,
            "death_overs_sr": 190.1,
            "boundary_pct": 68.1,
            "bowling_avg": None,
            "economy": None,
            "wickets": None,
            "bowling_sr": None,
            "death_overs_economy": None,
            "dot_ball_pct": None,
            "match_winning_innings": 15,
            "base_impact_score": 90.2
        }
    ]
    
    out_path = data_dir / "player_stats.json"
    with open(out_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Saved {len(stats)} player stats to {out_path}")

if __name__ == "__main__":
    run_scrape()
