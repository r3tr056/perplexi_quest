import uuid
import logging
from typing import Dict, List, Any, Set
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import json

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, JSON, Text, Boolean

from app.db.models import CollaborativeResearchSession
from app.core.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)

class CollaborationRole(str, Enum):
    OWNER = "owner"
    COLLABORATOR = "collaborator"
    VIEWER = "viewer"
    REVIEWER = "reviewer"

class ActivityType(str, Enum):
    JOIN_SESSION = "join_session"
    LEAVE_SESSION = "leave_session"
    ADD_RESEARCH = "add_research"
    EDIT_CONTENT = "edit_content"
    ADD_COMMENT = "add_comment"
    UPDATE_PLAN = "update_plan"
    EXPORT_DATA = "export_data"
    VALIDATE_CLAIM = "validate_claim"

@dataclass
class CollaborationUser:
    user_id: str
    username: str
    role: CollaborationRole
    avatar_url: str = ""
    is_online: bool = True
    last_activity: datetime = field(default_factory=datetime.utcnow)
    current_location: str = ""

@dataclass
class CollaborationActivity:
    activity_id: str
    user_id: str
    username: str
    activity_type: ActivityType
    content: Dict[str, Any]
    timestamp: datetime
    session_id: str

@dataclass
class CollaborationConflict:
    conflict_id: str
    session_id: str
    section_id: str
    user1_id: str
    user2_id: str
    conflict_type: str
    content1: Dict[str, Any]
    content2: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False

class CollaborationSessionManager:
    def __init__(self, connection_manager: ConnectionManager, db_session: AsyncSession):
        self.connection_manager = connection_manager
        self.db_session = db_session
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, Set[str]] = {}
        self.session_locks: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.active_conflicts: Dict[str, CollaborationConflict] = {}
        self.recent_activities: Dict[str, List[CollaborationActivity]] = {}

    async def create_collaborative_session(
        self, 
        title: str, 
        description: str, 
        owner_id: str, 
        initial_research_data: Dict[str, Any] = None
    ) -> str:
        session_id = f"collab_{uuid.uuid4().hex[:12]}"
        session = CollaborativeResearchSession(
            session_id=session_id,
            title=title,
            description=description,
            owner_id=owner_id,
            research_data=initial_research_data or {},
            permissions={
                "allow_public_view": False,
                "require_approval_for_edits": False,
                "max_collaborators": 10
            },
            settings={
                "auto_save_interval": 30,
                "conflict_resolution": "manual",
                "activity_retention_days": 30
            }
        )
        
        self.db_session.add(session)
        await self.db_session.commit()
        self.active_sessions[session_id] = {
            "session": session,
            "users": {},
            "current_state": initial_research_data or {},
            "pending_changes": {},
            "last_sync": datetime.now(timezone.utc)
        }
        self.session_locks[session_id] = {}
        self.recent_activities[session_id] = []
        return session_id

    async def join_session(
        self, 
        session_id: str, 
        user_id: str, 
        username: str, 
        websocket: WebSocket,
        role: CollaborationRole = CollaborationRole.VIEWER
    ) -> bool:
        try:
            if not await self._validate_session_access(session_id, user_id, role):
                return False
            user = CollaborationUser(
                user_id=user_id,
                username=username,
                role=role,
                is_online=True,
                last_activity=datetime.utcnow(),
                current_location="dashboard"
            )
            if session_id not in self.active_sessions:
                await self._load_session(session_id)
            self.active_sessions[session_id]["users"][user_id] = user
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)
            await self.connection_manager.connect(websocket, f"collab_{session_id}")
            await self._send_session_state(session_id, user_id)
            await self._broadcast_user_activity(
                session_id, 
                user_id, 
                ActivityType.JOIN_SESSION,
                {"username": username, "role": role.value}
            )
            await self._log_activity(
                session_id, user_id, username, 
                ActivityType.JOIN_SESSION, 
                {"role": role.value}
            )
            return True
        except Exception as e:
            logger.error(f"Error joining session {session_id}: {str(e)}")
            return False

    async def leave_session(self, session_id: str, user_id: str) -> bool:
        try:
            if session_id not in self.active_sessions:
                return False
            session_data = self.active_sessions[session_id]
            if user_id not in session_data["users"]:
                return False
            user = session_data["users"][user_id]
            username = user.username
            await self._release_user_locks(session_id, user_id)
            del session_data["users"][user_id]
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            await self.connection_manager.disconnect(f"collab_{session_id}", user_id)
            await self._broadcast_user_activity(
                session_id, 
                user_id, 
                ActivityType.LEAVE_SESSION,
                {"username": username}
            )
            await self._log_activity(
                session_id, user_id, username, 
                ActivityType.LEAVE_SESSION, 
                {}
            )
            return True
        except Exception as e:
            logger.error(f"Error leaving session {session_id}: {str(e)}")
            return False

    async def handle_real_time_edit(
        self, 
        session_id: str, 
        user_id: str, 
        section_id: str,
        edit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            if not await self._validate_edit_permission(session_id, user_id, section_id):
                return {"success": False, "error": "Insufficient permissions"}
            conflict = await self._check_edit_conflict(session_id, section_id, user_id, edit_data)
            if conflict:
                conflict_resolution = await self._handle_edit_conflict(conflict)
                return {
                    "success": False, 
                    "conflict": True,
                    "conflict_data": conflict_resolution
                }
            
            lock_acquired = await self._acquire_section_lock(session_id, section_id, user_id)
            if not lock_acquired:
                return {"success": False, "error": "Section is locked by another user"}
            
            success = await self._apply_edit(session_id, section_id, edit_data, user_id)
            if success:
                await self._broadcast_edit(session_id, user_id, section_id, edit_data)
                user = self.active_sessions[session_id]["users"][user_id]
                await self._log_activity(
                    session_id, user_id, user.username,
                    ActivityType.EDIT_CONTENT,
                    {"section_id": section_id, "edit_type": edit_data.get("type", "unknown")}
                )
                return {"success": True, "edit_id": str(uuid.uuid4())}
            else:
                return {"success": False, "error": "Failed to apply edit"}
        except Exception as e:
            logger.error(f"Error handling real-time edit: {str(e)}")
            return {"success": False, "error": str(e)}

    async def add_collaborative_comment(
        self,
        session_id: str,
        user_id: str,
        section_id: str,
        comment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            comment_id = f"comment_{uuid.uuid4().hex[:8]}"
            user = self.active_sessions[session_id]["users"][user_id]
            comment = {
                "comment_id": comment_id,
                "user_id": user_id,
                "username": user.username,
                "content": comment_data.get("content", ""),
                "section_id": section_id,
                "timestamp": datetime.utcnow().isoformat(),
                "replies": [],
                "resolved": False,
                "tags": comment_data.get("tags", [])
            }
            session_state = self.active_sessions[session_id]["current_state"]
            if "comments" not in session_state:
                session_state["comments"] = {}
            
            session_state["comments"][comment_id] = comment
            await self._broadcast_comment(session_id, comment)
            await self._log_activity(
                session_id, user_id, user.username,
                ActivityType.ADD_COMMENT,
                {"section_id": section_id, "comment_id": comment_id}
            )
            return {"success": True, "comment_id": comment_id, "comment": comment}
        except Exception as e:
            logger.error(f"Error adding collaborative comment: {str(e)}")
            return {"success": False, "error": str(e)}

    async def sync_research_state(self, session_id: str) -> Dict[str, Any]:
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}
            
            session_data = self.active_sessions[session_id]
            current_state = session_data["current_state"]
            if session_data["pending_changes"]:
                for change_id, change in session_data["pending_changes"].items():
                    await self._apply_pending_change(session_id, change)
                session_data["pending_changes"] = {}

            await self._persist_session_state(session_id, current_state)
            session_data["last_sync"] = datetime.now(timezone.utc)
            await self._broadcast_sync_complete(session_id)
            return {
                "success": True, 
                "sync_timestamp": session_data["last_sync"].isoformat(),
                "state_checksum": self._calculate_state_checksum(current_state)
            }
        except Exception as e:
            logger.error(f"Error syncing research state: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        try:
            if session_id not in self.active_sessions:
                return {"error": "Session not found"}
            session_data = self.active_sessions[session_id]
            activities = self.recent_activities.get(session_id, [])
            analytics = {
                "session_info": {
                    "session_id": session_id,
                    "title": session_data["session"].title,
                    "created_at": session_data["session"].created_at.isoformat(),
                    "last_sync": session_data["last_sync"].isoformat()
                },
                "collaboration_metrics": {
                    "total_users": len(session_data["users"]),
                    "online_users": len([u for u in session_data["users"].values() if u.is_online]),
                    "total_activities": len(activities),
                    "edit_count": len([a for a in activities if a.activity_type == ActivityType.EDIT_CONTENT]),
                    "comment_count": len([a for a in activities if a.activity_type == ActivityType.ADD_COMMENT])
                },
                "active_users": [
                    {
                        "user_id": user.user_id,
                        "username": user.username,
                        "role": user.role.value,
                        "is_online": user.is_online,
                        "last_activity": user.last_activity.isoformat(),
                        "current_location": user.current_location
                    }
                    for user in session_data["users"].values()
                ],
                "recent_activities": [
                    {
                        "activity_id": activity.activity_id,
                        "user_id": activity.user_id,
                        "username": activity.username,
                        "activity_type": activity.activity_type.value,
                        "timestamp": activity.timestamp.isoformat(),
                        "content": activity.content
                    }
                    for activity in activities[-20:]
                ],
                "conflicts": [
                    {
                        "conflict_id": conflict.conflict_id,
                        "section_id": conflict.section_id,
                        "users": [conflict.user1_id, conflict.user2_id],
                        "conflict_type": conflict.conflict_type,
                        "timestamp": conflict.timestamp.isoformat(),
                        "resolved": conflict.resolved
                    }
                    for conflict in self.active_conflicts.values()
                    if conflict.session_id == session_id
                ]
            }
            return analytics
        except Exception as e:
            logger.error(f"Error getting session analytics: {str(e)}")
            return {"error": str(e)}

    async def _validate_session_access(self, session_id: str, user_id: str, role: CollaborationRole) -> bool:
        return True

    async def _load_session(self, session_id: str):
        pass

    async def _send_session_state(self, session_id: str, user_id: str):
        session_data = self.active_sessions[session_id]
        state_message = {
            "type": "session_state",
            "session_id": session_id,
            "current_state": session_data["current_state"],
            "users": [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "role": user.role.value,
                    "is_online": user.is_online,
                    "current_location": user.current_location
                }
                for user in session_data["users"].values()
            ]
        }
        await self.connection_manager.send_personal_message(
            json.dumps(state_message), f"collab_{session_id}", user_id
        )

    async def _broadcast_user_activity(self, session_id: str, user_id: str, activity_type: ActivityType, content: Dict[str, Any]):
        message = {
            "type": "user_activity",
            "session_id": session_id,
            "user_id": user_id,
            "activity_type": activity_type.value,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.connection_manager.broadcast_to_group(json.dumps(message), f"collab_{session_id}")

    async def _log_activity(self, session_id: str, user_id: str, username: str, activity_type: ActivityType, content: Dict[str, Any]):
        activity = CollaborationActivity(
            activity_id=str(uuid.uuid4()),
            user_id=user_id,
            username=username,
            activity_type=activity_type,
            content=content,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id
        )
        if session_id not in self.recent_activities:
            self.recent_activities[session_id] = []
        self.recent_activities[session_id].append(activity)
        if len(self.recent_activities[session_id]) > 100:
            self.recent_activities[session_id] = self.recent_activities[session_id][-100:]