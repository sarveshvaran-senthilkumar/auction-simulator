import json
import os
from pathlib import Path

def run_scrape():
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock data output representing Wikipedia venue stats
    venues = [
        {
            "franchise_code": "DC",
            "ground_name": "Arun Jaitley Stadium",
            "avg_first_innings_score": 165.5,
            "chase_success_pct": 55.0,
            "pitch_tendency": "SPIN_FRIENDLY",
            "boundary_size_category": "SMALL",
            "source_url": "https://en.wikipedia.org/wiki/Arun_Jaitley_Stadium"
        },
        {
            "franchise_code": "RR",
            "ground_name": "Sawai Mansingh Stadium",
            "avg_first_innings_score": 158.2,
            "chase_success_pct": 60.5,
            "pitch_tendency": "PACE_FRIENDLY",
            "boundary_size_category": "LARGE",
            "source_url": "https://en.wikipedia.org/wiki/Sawai_Mansingh_Stadium"
        }
    ]
    
    out_path = data_dir / "venues.json"
    with open(out_path, "w") as f:
        json.dump(venues, f, indent=2)
    print(f"Saved {len(venues)} venues to {out_path}")

if __name__ == "__main__":
    run_scrape()
