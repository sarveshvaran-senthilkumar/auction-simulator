"""Drives a complete AI-only auction through the engine and prints the outcome.

    python scripts/smoke_auction.py

Verifies the plan's manual checks: squad caps, overseas caps, purse floors, RTM
consumption and AI squad-composition sanity -- without needing a browser.
"""

import asyncio
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402

# Fast-forward the clock so a 200+ lot auction finishes in seconds.
settings.BID_TIMER_SECONDS = 1
settings.BID_RESET_SECONDS = 1
settings.MAX_LOT_SECONDS = 8
settings.RETENTION_TIMEOUT_SECONDS = 1
settings.RTM_DECISION_SECONDS = 1
settings.AI_MIN_DELAY_MS = 10
settings.AI_MAX_DELAY_MS = 90

from app.db.database import AsyncSessionLocal  # noqa: E402
from app.db.models import Room, RoomStatus, Team, User  # noqa: E402
from app.engine.auction_engine import auction_engine  # noqa: E402

FRANCHISES = ["CSK", "MI", "RCB", "KKR", "DC", "RR", "PBKS", "SRH", "LSG", "GT"]

events = Counter()
sold_log = []


async def emitter(room_code, event, payload, to_user=None):
    events[event] += 1
    if event == "LOT_SOLD":
        sold_log.append((payload["player"]["name"], payload["franchise_code"],
                         payload["price_lakh"], payload["acquisition_type"]))


async def main() -> None:
    auction_engine.set_emitter(emitter)

    async with AsyncSessionLocal() as session:
        # Make the script re-runnable against an already-seeded database.
        from sqlalchemy import delete, select
        prior = (await session.execute(
            select(Room).where(Room.room_code == "SMOKE1")
        )).scalar_one_or_none()
        if prior is not None:
            await session.execute(delete(Team).where(Team.room_id == prior.id))
            await session.execute(delete(Room).where(Room.id == prior.id))
            await session.commit()

        user = User(display_name="Smoke")
        session.add(user)
        await session.flush()
        room = Room(room_code="SMOKE1", host_user_id=user.id, status=RoomStatus.LOBBY)
        session.add(room)
        await session.flush()
        for code in FRANCHISES:
            session.add(Team(
                room_id=room.id, franchise_code=code,
                purse_remaining_lakh=settings.DEFAULT_PURSE_LAKH, is_ai=True,
            ))
        await session.commit()

    print("starting retention...")
    state = await auction_engine.start_retention("SMOKE1")

    last_progress = (-1, 0.0)
    for i in range(2400):
        if state.status == "COMPLETED":
            break
        if i % 40 == 0 and i:
            print(f"  ... {state.lots_done}/{state.total_lots} lots "
                  f"({events['BID_PLACED']} bids)", flush=True)
        if state.lots_done != last_progress[0]:
            last_progress = (state.lots_done, asyncio.get_running_loop().time())
        elif asyncio.get_running_loop().time() - last_progress[1] > 45:
            print(f"!! STALLED at lot {state.lots_done}/{state.total_lots} "
                  f"lot_status={state.lot.status if state.lot else None}")
            task = auction_engine.tasks.get("SMOKE1")
            print(f"   task done={task.done() if task else 'MISSING'}")
            if task and task.done():
                print(f"   task exception={task.exception()!r}")
            elif task:
                import io
                buf = io.StringIO()
                task.print_stack(file=buf)
                print("   stack:\n" + buf.getvalue())
            print(f"   room lock held={auction_engine.lock('SMOKE1').locked()}")
            break
        await asyncio.sleep(0.5)
    else:
        print(f"!! did not finish, stuck at {state.status} "
              f"lot {state.lots_done}/{state.total_lots}")

    print(f"\nstatus={state.status}  lots {state.lots_done}/{state.total_lots}")
    print(f"events: {dict(events)}\n")

    results = auction_engine.results(state)
    problems = []

    print(f"{'TEAM':6s} {'SQD':>4s} {'OS':>3s} {'RTM':>4s} {'SPENT':>8s} {'LEFT':>8s} {'IMPACT':>7s}  ROLES")
    for t in results["teams"]:
        roles = t["role_counts"]
        print(f"{t['franchise_code']:6s} {t['squad_size']:4d} {t['overseas_used']:3d} "
              f"{t['rtm_cards']:4d} {t['spent_lakh']/100:7.2f}cr {t['purse_remaining_lakh']/100:7.2f}cr "
              f"{t['squad_impact']:7.1f}  "
              + " ".join(f"{k[:3]}:{v}" for k, v in sorted(roles.items())))

        if t["squad_size"] > settings.MAX_SQUAD_SIZE:
            problems.append(f"{t['franchise_code']} squad {t['squad_size']} > 25")
        if t["overseas_used"] > settings.MAX_OVERSEAS:
            problems.append(f"{t['franchise_code']} overseas {t['overseas_used']} > 8")
        if t["purse_remaining_lakh"] < 0:
            problems.append(f"{t['franchise_code']} purse went negative")
        # The legal minimum scales with the format's pool size, so compare
        # against what this room actually set rather than a fixed number.
        if t["squad_size"] < state.min_squad_size - 3:
            problems.append(
                f"{t['franchise_code']} filled {t['squad_size']}, "
                f"well short of min {state.min_squad_size}"
            )
        for role, count in roles.items():
            if count > 11:
                problems.append(f"{t['franchise_code']} hoarded {count} {role}s")

    rtm_buys = [s for s in sold_log if s[3] == "RTM"]
    print("\ntop 8 sales:")
    for name, fr, price, kind in sorted(sold_log, key=lambda s: -s[2])[:8]:
        print(f"  {price/100:6.2f}cr  {name:24s} -> {fr}  ({kind})")
    print(f"\nRTM buybacks: {len(rtm_buys)}")
    for name, fr, price, _ in rtm_buys[:5]:
        print(f"  {price/100:6.2f}cr  {name:24s} -> {fr}")

    unique_squads = len({tuple(sorted(t['role_counts'].items())) for t in results["teams"]})
    print(f"\nAI diversity: {unique_squads}/10 distinct role shapes")

    print("\n" + ("PROBLEMS:\n  " + "\n  ".join(problems) if problems else "all invariants held"))


if __name__ == "__main__":
    asyncio.run(main())
