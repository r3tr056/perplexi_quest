import asyncio
import json
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)

class StreamType(str, Enum):
    THOUGHT = "thought"
    PROGRESS = "progress"
    RESULT = "result"
    ERROR = "error"
    COMPLETION = "completion"
    USER_NOTIFICATION = "user_notification"

@dataclass
class ThoughtStream:
    """Represents a streaming thought from an agent"""
    agent: str
    step: str
    thought: str
    confidence: float
    timestamp: str = "2025-05-28 17:46:02"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProgressStream:
    """Represents progress update stream"""
    step: str
    progress: int  # 0-100
    message: str
    estimated_completion: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class StreamingManager:

    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.stream_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self.user_subscriptions: Dict[str, List[str]] = {}

    async def start_session(self, session_id: str, user_id: str, title: str) -> bool:
        try:
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "title": title,
                "started_at": datetime.utcnow().isoformat(),
                "status": "active",
                "stream_count": 0
            }

            self.stream_buffers[session_id] = []
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = []
            self.user_subscriptions[user_id].append(session_id)
            
            await self._send_stream(session_id, {
                "type": StreamType.USER_NOTIFICATION,
                "content": {
                    "message": f"Research session started: {title}",
                    "session_id": session_id,
                    "status": "started"
                },
                "timestamp": "2025-05-28 17:46:02"
            })
            logger.info(f"Streaming session started: {session_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start streaming session: {str(e)}")
            return False

    async def stream_thought(self, session_id: str, thought_stream: ThoughtStream):

        if session_id not in self.active_sessions:
            logger.warning(f"Attempted to stream to inactive session: {session_id}")
            return
        try:
            stream_data = {
                "type": StreamType.THOUGHT,
                "content": asdict(thought_stream),
                "timestamp": "2025-05-28 17:46:02",
                "session_id": session_id
            }
            await self._send_stream(session_id, stream_data)
            self._buffer_stream(session_id, stream_data)
            self.active_sessions[session_id]["stream_count"] += 1
        except Exception as e:
            logger.error(f"Failed to stream thought: {str(e)}")

    async def stream_progress(self, session_id: str, progress_data: Dict[str, Any]):
        if session_id not in self.active_sessions:
            return
        try:
            stream_data = {
                "type": StreamType.PROGRESS,
                "content": progress_data,
                "timestamp": "2025-05-28 17:46:02",
                "session_id": session_id
            }
            await self._send_stream(session_id, stream_data)
            self._buffer_stream(session_id, stream_data)
        except Exception as e:
            logger.error(f"Failed to stream progress: {str(e)}")

    async def stream_result(self, session_id: str, result_data: Dict[str, Any]):
        if session_id not in self.active_sessions:
            return
        try:
            stream_data = {
                "type": StreamType.RESULT,
                "content": result_data,
                "timestamp": "2025-05-28 17:46:02",
                "session_id": session_id
            }
            await self._send_stream(session_id, stream_data)
            self._buffer_stream(session_id, stream_data)
        except Exception as e:
            logger.error(f"Failed to stream result: {str(e)}")

    async def stream_error(self, session_id: str, error_data: Dict[str, Any]):
        if session_id not in self.active_sessions:
            return
        try:
            stream_data = {
                "type": StreamType.ERROR,
                "content": error_data,
                "timestamp": "2025-05-28 17:46:02",
                "session_id": session_id
            }
            await self._send_stream(session_id, stream_data)
            self._buffer_stream(session_id, stream_data)
        except Exception as e:
            logger.error(f"Failed to stream error: {str(e)}")

    async def stream_completion(self, session_id: str, completion_data: Dict[str, Any]):
        if session_id not in self.active_sessions:
            return
        try:
            stream_data = {
                "type": StreamType.COMPLETION,
                "content": completion_data,
                "timestamp": "2025-05-28 17:46:02",
                "session_id": session_id
            }
            await self._send_stream(session_id, stream_data)
            self._buffer_stream(session_id, stream_data)
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["status"] = "completed"
                self.active_sessions[session_id]["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Failed to stream completion: {str(e)}")

    async def end_session(self, session_id: str):        
        try:
            if session_id in self.active_sessions:
                user_id = self.active_sessions[session_id]["user_id"]
                await self._send_stream(session_id, {
                    "type": StreamType.USER_NOTIFICATION,
                    "content": {
                        "message": "Research session completed",
                        "session_id": session_id,
                        "status": "ended",
                        "total_streams": self.active_sessions[session_id]["stream_count"]
                    },
                    "timestamp": "2025-05-28 17:46:02"
                })
                del self.active_sessions[session_id]
                if user_id in self.user_subscriptions:
                    if session_id in self.user_subscriptions[user_id]:
                        self.user_subscriptions[user_id].remove(session_id)
                logger.info(f"Streaming session ended: {session_id}")
        except Exception as e:
            logger.error(f"Failed to end streaming session: {str(e)}")

    async def replay_session_streams(self, session_id: str, user_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        if session_id not in self.stream_buffers:
            return
        if user_id not in self.user_subscriptions or session_id not in self.user_subscriptions[user_id]:
            return
        try:
            for stream_data in self.stream_buffers[session_id]:
                yield stream_data
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to replay session streams: {str(e)}")

    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id].copy()
        session_data["stream_buffer_size"] = len(self.stream_buffers.get(session_id, []))
        
        return session_data

    async def get_user_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        user_sessions = []
        
        if user_id in self.user_subscriptions:
            for session_id in self.user_subscriptions[user_id]:
                if session_id in self.active_sessions:
                    session_data = self.active_sessions[session_id].copy()
                    session_data["session_id"] = session_id
                    user_sessions.append(session_data)
        
        return user_sessions

    async def _send_stream(self, session_id: str, stream_data: Dict[str, Any]):
        if session_id not in self.active_sessions:
            return
        try:
            stream_data["stream_id"] = str(uuid.uuid4())
            stream_data["sequence"] = self.active_sessions[session_id]["stream_count"]
            await self.websocket_manager.broadcast_to_group(
                json.dumps(stream_data),
                f"stream_{session_id}"
            )
        except Exception as e:
            logger.error(f"Failed to send stream via WebSocket: {str(e)}")

    def _buffer_stream(self, session_id: str, stream_data: Dict[str, Any]):
        if session_id not in self.stream_buffers:
            self.stream_buffers[session_id] = []
        if len(self.stream_buffers[session_id]) >= 1000:
            self.stream_buffers[session_id] = self.stream_buffers[session_id][-999:]
        self.stream_buffers[session_id].append(stream_data)

    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        try:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, session_data in self.active_sessions.items():
                started_at = datetime.fromisoformat(session_data["started_at"])
                age_hours = (current_time - started_at).total_seconds() / 3600
                
                if age_hours > max_age_hours and session_data["status"] != "active":
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                await self.end_session(session_id)
                if session_id in self.stream_buffers:
                    del self.stream_buffers[session_id]
            
            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {str(e)}")