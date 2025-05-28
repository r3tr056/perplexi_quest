from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import contextvars
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.auth_service import AuthenticationService
from app.db.database import get_db_session

user_context: contextvars.ContextVar = contextvars.ContextVar('user_context')

@dataclass
class UserContext:
	user_id: str
	email: str
	username: str
	full_name: str
	is_verified: bool
	is_superuser: bool
	subscription_tier: str
	research_interests: list
	institution: Optional[str] = None
	
	# Request metadata
	request_id: str = field(default_factory=lambda: f"req_{datetime.utcnow().timestamp()}")
	timestamp: str = field(default_factory=lambda: "2025-05-27 19:54:25")
	ip_address: Optional[str] = None
	user_agent: Optional[str] = None
	
	# Permissions and scopes
	scopes: list = field(default_factory=list)
	rate_limit: int = 100
	
	# Session information
	auth_method: str = "jwt"  # jwt, api_key
	session_data: Dict[str, Any] = field(default_factory=dict)

class UserContextManager:
	"""Manages user context throughout request lifecycle"""
	
	def __init__(self):
		self.security = HTTPBearer()

	async def get_current_user_context(
		self, 
		request: Request,
		credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
		db_session: AsyncSession = Depends(get_db_session)
	) -> UserContext:
		try:
			auth_service = AuthenticationService(db_session)
			token = credentials.credentials
			user_data = await auth_service.verify_token(token)
			if not user_data:
				api_key_data = await auth_service.verify_api_key(token)
				if not api_key_data:
					raise HTTPException(
						status_code=status.HTTP_401_UNAUTHORIZED,
						detail="Invalid authentication credentials",
						headers={"WWW-Authenticate": "Bearer"},
					)
				context = UserContext(
					user_id=api_key_data["user_id"],
					email=api_key_data["email"],
					username=api_key_data["username"],
					full_name="API User",
					is_verified=True,
					is_superuser=False,
					subscription_tier=api_key_data["subscription_tier"],
					research_interests=[],
					scopes=api_key_data["scopes"],
					rate_limit=api_key_data["rate_limit"],
					auth_method="api_key",
					ip_address=request.client.host if request.client else None,
					user_agent=request.headers.get("user-agent")
				)
			else:
				context = UserContext(
					user_id=user_data["user_id"],
					email=user_data["email"],
					username=user_data["username"],
					full_name=user_data["full_name"],
					is_verified=user_data["is_verified"],
					is_superuser=user_data["is_superuser"],
					subscription_tier=user_data["subscription_tier"],
					research_interests=user_data["research_interests"],
					institution=user_data["institution"],
					auth_method="jwt",
					ip_address=request.client.host if request.client else None,
					user_agent=request.headers.get("user-agent")
				)
			user_context.set(context)
			return context
		except HTTPException:
			raise
		except Exception as e:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail=f"Authentication error: {str(e)}"
			)

	def get_current_context(self) -> Optional[UserContext]:
		try:
			return user_context.get()
		except LookupError:
			return None

	def require_scope(self, required_scope: str):
		def _require_scope(context: UserContext = Depends(self.get_current_user_context)):
			if context.auth_method == "api_key" and required_scope not in context.scopes:
				raise HTTPException(
					status_code=status.HTTP_403_FORBIDDEN,
					detail=f"Insufficient permissions. Required scope: {required_scope}"
				)
			return context
		return _require_scope

	def require_verification(self):
		def _require_verification(context: UserContext = Depends(self.get_current_user_context)):
			if not context.is_verified:
				raise HTTPException(
					status_code=status.HTTP_403_FORBIDDEN,
					detail="Email verification required"
				)
			return context
		return _require_verification

	def require_subscription_tier(self, min_tier: str):
		tier_order = {"free": 0, "pro": 1, "enterprise": 2}
		
		def _require_tier(context: UserContext = Depends(self.get_current_user_context)):
			user_tier_level = tier_order.get(context.subscription_tier, 0)
			required_tier_level = tier_order.get(min_tier, 0)
			
			if user_tier_level < required_tier_level:
				raise HTTPException(
					status_code=status.HTTP_403_FORBIDDEN,
					detail=f"Subscription upgrade required. Minimum tier: {min_tier}"
				)
			return context
		return _require_tier

user_manager = UserContextManager()

def get_current_user(context: UserContext = Depends(user_manager.get_current_user_context)) -> UserContext:
	return context

def get_verified_user(context: UserContext = Depends(user_manager.require_verification())) -> UserContext:
	return context

def require_research_scope(context: UserContext = Depends(user_manager.require_scope("research:write"))) -> UserContext:
	return context

def require_pro_subscription(context: UserContext = Depends(user_manager.require_subscription_tier("pro"))) -> UserContext:
	return context