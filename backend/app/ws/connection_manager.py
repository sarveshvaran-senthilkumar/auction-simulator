"""Tracks live sockets per room and fans events out."""

import asyncio
import json
from typing import Dict, List, Optional, Set

from fastapi import WebSocket


class Connection:
    def __init__(self, socket: WebSocket, user_id: Optional[str]) -> None:
        self.socket = socket
        self.user_id = user_id


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: Dict[str, List[Connection]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, room_code: str, socket: WebSocket, user_id: Optional[str]) -> Connection:
        await socket.accept()
        conn = Connection(socket, user_id)
        async with self._lock:
            self.rooms.setdefault(room_code, []).append(conn)
        return conn

    async def disconnect(self, room_code: str, conn: Connection) -> None:
        async with self._lock:
            conns = self.rooms.get(room_code, [])
            if conn in conns:
                conns.remove(conn)
            if not conns:
                self.rooms.pop(room_code, None)

    def user_ids(self, room_code: str) -> Set[str]:
        return {c.user_id for c in self.rooms.get(room_code, []) if c.user_id}

    async def send(
        self, room_code: str, event: str, payload: dict, to_user: Optional[str] = None
    ) -> None:
        message = json.dumps({"type": event, "payload": payload})
        targets = [
            c for c in list(self.rooms.get(room_code, []))
            if to_user is None or c.user_id == to_user
        ]
        dead: List[Connection] = []
        for conn in targets:
            try:
                await conn.socket.send_text(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            await self.disconnect(room_code, conn)


manager = ConnectionManager()
