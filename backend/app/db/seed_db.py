import json
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

# Assuming relative imports work or run as module
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from app.db.database import engine, Base, AsyncSessionLocal
from app.db.models import Player, Squad2024Entry

async def seed():
    data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # Load master pool
        if (data_dir / "master_pool.json").exists():
            with open(data_dir / "master_pool.json", "r") as f:
                players_data = json.load(f)
                
            player_map = {}
            for p in players_data:
                player = Player(**p)
                session.add(player)
                player_map[p['name']] = player
                
            await session.commit()
            print(f"Seeded {len(players_data)} players.")
            
        # Load squad 2024 entries
        if (data_dir / "squads_2024.json").exists():
            with open(data_dir / "squads_2024.json", "r") as f:
                squads_data = json.load(f)
                
            for s in squads_data:
                # Find player ID
                player = player_map.get(s['player_name'])
                if player:
                    entry = Squad2024Entry(
                        franchise_code=s['franchise'],
                        player_id=player.id,
                        role=s['role'],
                        was_capped=s['was_capped']
                    )
                    session.add(entry)
                    
            await session.commit()
            print(f"Seeded {len(squads_data)} 2024 squad entries.")

if __name__ == "__main__":
    asyncio.run(seed())
