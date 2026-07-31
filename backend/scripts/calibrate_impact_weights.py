import json
import os
from pathlib import Path

def run_calibration():
    # Mock script to generate the calibrated weights.json based on historical sold prices
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    weights = {
        "Batter": {
            "batting_avg": 0.18,
            "strike_rate": 0.22,
            "powerplay_sr": 0.12,
            "boundary_pct": 0.10,
            "match_winning_innings": 0.08,
            "experience": 0.15,
            "recency": 0.10,
            "context": 0.05
        },
        "Bowler": {
            "wickets": 0.20,
            "economy": 0.22,
            "bowling_avg": 0.15,
            "dot_ball_pct": 0.10,
            "death_overs_economy": 0.13,
            "experience": 0.10,
            "recency": 0.05,
            "context": 0.05
        },
        "All-Rounder": {
            "batting_avg": 0.15,
            "strike_rate": 0.15,
            "wickets": 0.15,
            "economy": 0.15,
            "match_winning_innings": 0.10,
            "experience": 0.10,
            "recency": 0.10,
            "context": 0.10
        },
        "Wicket-Keeper": {
            "batting_avg": 0.20,
            "strike_rate": 0.20,
            "powerplay_sr": 0.15,
            "boundary_pct": 0.10,
            "keeping_bonus": 0.15,
            "experience": 0.10,
            "recency": 0.10,
            "context": 0.00
        }
    }
    
    out_path = data_dir / "weights.json"
    with open(out_path, "w") as f:
        json.dump(weights, f, indent=2)
    print(f"Saved calibrated weights to {out_path}")

if __name__ == "__main__":
    run_calibration()
