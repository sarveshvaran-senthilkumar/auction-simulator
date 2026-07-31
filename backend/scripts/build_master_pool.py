import json
from pathlib import Path

def build_master_pool():
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    
    with open(data_dir / "auction_list_2025.json", "r") as f:
        auction_list = json.load(f)
        
    with open(data_dir / "squads_2024.json", "r") as f:
        squads = json.load(f)

    master_pool = {}
    
    # Process auction list first
    for p in auction_list:
        key = f"{p['name']}_{p['nationality']}"
        p["is_fallback_price"] = False
        master_pool[key] = p
        
    # Process squads to find players not in the auction list
    for s in squads:
        # Simplistic matching for mock
        name = s['player_name']
        # we don't have nationality in squad list usually, assume India for this mock logic
        key = f"{name}_India"
        if key not in master_pool and f"{name}_England" not in master_pool:
            # Player from 2024 not in 2025 auction
            master_pool[key] = {
                "name": name,
                "nationality": "India", # fallback
                "role": s["role"],
                "is_capped": s["was_capped"],
                "base_price_lakh": 30, # lowest bracket fallback
                "set_name": "Unknown",
                "is_overseas": False,
                "age": 25,
                "is_fallback_price": True
            }
            
    out_path = data_dir / "master_pool.json"
    with open(out_path, "w") as f:
        json.dump(list(master_pool.values()), f, indent=2)
        
    print(f"Master pool built with {len(master_pool)} players.")

if __name__ == "__main__":
    build_master_pool()
