from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime, JSON, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # User profile
    full_name = Column(String(100), nullable=True)
    organization = Column(String, nullable=True)
    role = Column(String(20), default="basic")
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    department = Column(String, nullable=True)
    research_interests = Column(JSON, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Account metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    timezone = Column(String, default="UTC")

    email_verified_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.now())
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String, nullable=True)

    total_research_sessions = Column(Integer, default=0)
    total_api_calls = Column(Integer, default=0)
    subscription_tier = Column(String, default="free")  # free, pro, enterprise
    
    # Relationships
    research_sessions = relationship("ResearchSession", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    user_preferences = relationship("UserPreferences", back_populates="user", uselist=False)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)
        self.password_changed_at = datetime.now()

    def generate_auth_token(self, secret_key: str, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(hours=24)
        
        payload = {
            "user_id": self.user_id,
            "email": self.email,
            "username": self.username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "sub": "auth_token"
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    def update_last_login(self):
        self.last_login = datetime.now()

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    preference_id = Column(String, primary_key=True, default=lambda: f"pref_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    
    # Research preferences
    default_research_type = Column(String, default="standard")
    default_target_audience = Column(String, default="general")
    preferred_citation_style = Column(String, default="apa")
    auto_save_enabled = Column(Boolean, default=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    collaboration_notifications = Column(Boolean, default=True)
    research_completion_notifications = Column(Boolean, default=True)
    weekly_summary_emails = Column(Boolean, default=False)
    
    # Interface preferences
    theme = Column(String, default="light")  # light, dark, auto
    language = Column(String, default="en")
    items_per_page = Column(Integer, default=20)
    
    # Privacy settings
    profile_visibility = Column(String, default="public")  # public, private, connections
    research_sharing_default = Column(String, default="private")
    
    # Integration settings
    connected_services = Column(JSON, default=dict)
    api_rate_limit_preference = Column(String, default="standard")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_preferences")

class APIKey(Base):
    __tablename__ = "api_keys"
    
    key_id = Column(String, primary_key=True, default=lambda: f"key_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False, unique=True)
    key_prefix = Column(String, nullable=False)  # First 8 characters for display
    
    # Permissions
    scopes = Column(JSON, default=list)  # ['research:read', 'research:write', 'export:all']
    
    # Status and limits
    is_active = Column(Boolean, default=True)
    rate_limit_per_hour = Column(Integer, default=100)
    total_requests = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class ResearchSession(Base):
    __tablename__ = "research_sessions"
    
    session_id = Column(String, primary_key=True, default=lambda: f"session_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    
    title = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    research_type = Column(String, default="standard")
    target_audience = Column(String, default="general")
    domain = Column(String, default="general")
    
    # Session status
    status = Column(String, default="active")  # active, completed, failed, archived
    progress = Column(Integer, default=0)  # 0-100
    
    # Research data
    research_plan = Column(JSON, nullable=True)
    research_results = Column(JSON, nullable=True)
    validation_results = Column(JSON, nullable=True)
    final_report = Column(JSON, nullable=True)
    quality_metrics = Column(JSON, nullable=True)
    
    # Collaboration
    is_collaborative = Column(Boolean, default=False)
    collaboration_settings = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Privacy and sharing
    visibility = Column(String, default="private")  # private, public, shared
    shared_with = Column(JSON, default=list)  # List of user IDs
    
    # Relationships
    user = relationship("User", back_populates="research_sessions")

class AgentExecutionModel(Base):
    __tablename__ = "agent_executions"
    
    execution_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    agent_name = Column(String, nullable=False)
    
    # Execution details
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    status = Column(String, default="pending")
    error_message = Column(Text, nullable=True)
    
    # Performance metrics
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    execution_time_seconds = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())


class CollaborativeResearchSession(Base):
    __tablename__ = "collaborative_sessions"
    
    session_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    research_data = Column(JSON)
    permissions = Column(JSON)
    settings = Column(JSON)