import json
import os
from pathlib import Path

# Mock script for scraping wikipedia
def run_scrape():
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock data output
    squads = [
        {
            "player_name": "Rishabh Pant",
            "franchise": "DC",
            "role": "Wicket-Keeper",
            "was_capped": True
        },
        {
            "player_name": "Jos Buttler",
            "franchise": "RR",
            "role": "Wicket-Keeper",
            "was_capped": True
        }
    ]
    
    out_path = data_dir / "squads_2024.json"
    with open(out_path, "w") as f:
        json.dump(squads, f, indent=2)
    print(f"Saved {len(squads)} squad entries to {out_path}")

if __name__ == "__main__":
    run_scrape()
