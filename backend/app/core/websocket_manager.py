from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")

    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            message_str = json.dumps(message)
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    print(f"Error broadcasting to session {session_id}: {e}")

    async def send_agent_update(self, session_id: str, agent_name: str, status: str, data: dict = None):
        message = {
            "type": "agent_update",
            "agent": agent_name,
            "status": status,
            "data": data or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast_to_session(session_id, message)