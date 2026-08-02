"""End-to-end check against a running server: HTTP room setup + live WebSocket play.

Simulates what a phone does -- create a room, claim a franchise, confirm
retentions over the socket, then bid on the first few lots.

    uvicorn app.main:app --port 8000     # in another terminal
    python scripts/smoke_client.py
"""

import asyncio
import json
import sys
import urllib.request
from collections import Counter

BASE = "http://127.0.0.1:8000"
WS = "ws://127.0.0.1:8000"


def post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}") as res:
        return json.load(res)


async def main() -> None:
    try:
        import websockets
    except ImportError:
        sys.exit("pip install websockets")

    room = post("/api/rooms", {"host_display_name": "Phone", "config": {"format": "QUICK"}})
    code, user_id = room["room_code"], room["host_user_id"]
    print(f"room {code}")

    joined = post(f"/api/rooms/{code}/join", {"franchise_code": "CSK", "user_id": user_id})
    team_id = next(t["id"] for t in joined["teams"] if t["franchise_code"] == "CSK")
    print(f"claimed CSK ({team_id[:8]})")

    pool = get(f"/api/rooms/{code}/retention-pool/{team_id}")
    top3 = [p["id"] for p in pool["players"][:3]]
    print(f"retention pool: {len(pool['players'])} players, keeping top 3")

    post(f"/api/rooms/{code}/start", {})
    print("retention phase open")

    events = Counter()
    seen_lots, my_bids, rejects = [], 0, []

    async with websockets.connect(f"{WS}/ws/auction/{code}?user_id={user_id}") as ws:
        await ws.send(json.dumps({
            "type": "RETENTION_CONFIRM", "payload": {"player_ids": top3},
        }))

        deadline = asyncio.get_running_loop().time() + 150
        next_bid = 0

        while asyncio.get_running_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=20)
            except asyncio.TimeoutError:
                print("!! no events for 20s")
                break

            msg = json.loads(raw)
            kind, payload = msg["type"], msg["payload"]
            events[kind] += 1

            if kind == "LOT_STARTED":
                seen_lots.append(payload["lot"]["player"]["name"])
                next_bid = payload["next_bid_lakh"]
                if len(seen_lots) >= 6:
                    break
            elif kind == "BID_PLACED":
                next_bid = payload["next_bid_lakh"]
            elif kind == "BID_REJECTED":
                rejects.append(payload["reason"])
            elif kind == "RTM_PROMPT":
                await ws.send(json.dumps({"type": "DECISION", "payload": {"choice": True}}))
                print(f"   answered RTM prompt for {payload['player']['name']}")
            elif kind == "RTM_COUNTER_PROMPT":
                await ws.send(json.dumps({"type": "DECISION", "payload": {"choice": False}}))

            # Try to win the second lot, to exercise the human bidding path.
            if len(seen_lots) == 2 and my_bids < 3 and kind in ("LOT_STARTED", "BID_PLACED"):
                await ws.send(json.dumps({
                    "type": "PLACE_BID", "payload": {"amount_lakh": next_bid},
                }))
                my_bids += 1

    state = get(f"/api/rooms/{code}/state")
    mine = next(t for t in state["teams"] if t["id"] == team_id)

    print(f"\nevents: {dict(events)}")
    print(f"lots seen: {seen_lots}")
    print(f"human bids sent: {my_bids}  rejected: {rejects}")
    print(f"format={state['auction_format']} total_lots={state['total_lots']} "
          f"min_squad={state['min_squad_size']}")
    print(f"CSK: squad={mine['squad_size']} purse={mine['purse_remaining_lakh']/100:.2f}cr "
          f"rtm={mine['rtm_cards']}")

    problems = []
    if mine["squad_size"] < 3:
        problems.append("retentions did not apply")
    if mine["rtm_cards"] != 3:
        problems.append(f"expected 3 RTM cards after 3 retentions, got {mine['rtm_cards']}")
    if not seen_lots:
        problems.append("no lots started")
    if state["total_lots"] > 90:
        problems.append(f"QUICK format gave {state['total_lots']} lots")
    if events["TIMER_TICK"] == 0:
        problems.append("no timer ticks reached the client")

    print("\n" + ("PROBLEMS:\n  " + "\n  ".join(problems) if problems else "client flow OK"))


if __name__ == "__main__":
    asyncio.run(main())
