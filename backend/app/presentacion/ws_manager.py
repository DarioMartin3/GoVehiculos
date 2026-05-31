from typing import Dict, Set
import asyncio
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self) -> None:
        # mapping: conversacion_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, conversacion_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            if conversacion_id not in self.active_connections:
                self.active_connections[conversacion_id] = set()
            self.active_connections[conversacion_id].add(websocket)

    async def disconnect(self, conversacion_id: int, websocket: WebSocket) -> None:
        async with self.lock:
            conns = self.active_connections.get(conversacion_id)
            if not conns:
                return
            conns.discard(websocket)
            if not conns:
                del self.active_connections[conversacion_id]

    async def broadcast_message(self, conversacion_id: int, message: dict) -> None:
        # Send JSON message to all connected websockets for the conversation
        conns = self.active_connections.get(conversacion_id) or set()
        if not conns:
            return
        data = message
        await asyncio.gather(*[ws.send_json(data) for ws in list(conns)], return_exceptions=True)


# single global manager
manager = ConnectionManager()
