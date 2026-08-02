"""WebSocket endpoint: routes client messages into the auction engine."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..engine.auction_engine import auction_engine
from .connection_manager import manager

router = APIRouter()

auction_engine.set_emitter(manager.send)


@router.websocket("/ws/auction/{room_code}")
async def auction_socket(websocket: WebSocket, room_code: str, user_id: str = ""):
    room_code = room_code.upper()
    conn = await manager.connect(room_code, websocket, user_id or None)

    try:
        room = await auction_engine.load_room(room_code)
    except KeyError:
        await websocket.send_json({"type": "ERROR", "payload": {"reason": "Room not found"}})
        await manager.disconnect(room_code, conn)
        await websocket.close()
        return

    my_team = room.team_by_user(user_id) if user_id else None
    if my_team:
        my_team.connected = True

    await websocket.send_json({
        "type": "SNAPSHOT",
        "payload": {
            "room": room.public(),
            "my_team_id": my_team.id if my_team else None,
        },
    })
    await manager.send(room_code, "ROOM_UPDATE", room.public())

    try:
        while True:
            message = await websocket.receive_json()
            await _handle(room_code, user_id, message, websocket)
    except WebSocketDisconnect:
        pass
    finally:
        if my_team:
            my_team.connected = any(
                c.user_id == user_id for c in manager.rooms.get(room_code, []) if c is not conn
            )
        await manager.disconnect(room_code, conn)
        await manager.send(room_code, "ROOM_UPDATE", room.public())


async def _handle(room_code: str, user_id: str, message: dict, websocket: WebSocket) -> None:
    kind = message.get("type")
    payload = message.get("payload") or {}
    room = auction_engine.get(room_code)
    if room is None:
        return

    team = room.team_by_user(user_id) if user_id else None

    if kind == "PLACE_BID":
        if team is None:
            return await _reject(websocket, "You are not controlling a franchise")
        ok, reason = await auction_engine.place_bid(room_code, team.id, payload.get("amount_lakh", 0))
        if not ok:
            await _reject(websocket, reason)

    elif kind == "RETENTION_CONFIRM":
        if team is None:
            return await _reject(websocket, "You are not controlling a franchise")
        ok, reason = await auction_engine.submit_retention(
            room_code, team.id, payload.get("player_ids", [])
        )
        if not ok:
            await _reject(websocket, reason)

    elif kind == "DECISION":
        # Answers both RTM_PROMPT and RTM_COUNTER_PROMPT.
        if team is not None:
            await auction_engine.resolve_decision(room_code, team.id, bool(payload.get("choice")))

    elif kind == "PING":
        await websocket.send_json({"type": "PONG", "payload": {}})


async def _reject(websocket: WebSocket, reason: str) -> None:
    await websocket.send_json({"type": "BID_REJECTED", "payload": {"reason": reason}})
