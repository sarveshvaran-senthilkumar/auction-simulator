import json
import os
from pathlib import Path

# Mock script since we don't have the real PDF and pdfplumber in this environment.
# In a real scenario, this would use pdfplumber to parse the BCCI PDF.
def run_scrape():
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock data output
    auction_list = [
        {
            "name": "Rishabh Pant",
            "nationality": "India",
            "role": "Wicket-Keeper",
            "is_capped": True,
            "base_price_lakh": 200,
            "set_name": "Marquee",
            "is_overseas": False,
            "age": 26
        },
        {
            "name": "Jos Buttler",
            "nationality": "England",
            "role": "Wicket-Keeper",
            "is_capped": True,
            "base_price_lakh": 200,
            "set_name": "Marquee",
            "is_overseas": True,
            "age": 33
        }
    ]
    
    out_path = data_dir / "auction_list_2025.json"
    with open(out_path, "w") as f:
        json.dump(auction_list, f, indent=2)
    print(f"Saved {len(auction_list)} players to {out_path}")

if __name__ == "__main__":
    run_scrape()
