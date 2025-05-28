from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import httpx
from datetime import datetime

from app.api.auth.auth_service import AuthenticationService
from app.api.auth.user_context import get_current_user, get_verified_user, UserContext
from app.db.database import get_db_session
from app.core.rate_limiter import RateLimiter

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
rate_limiter = RateLimiter()

class UserRegistration(BaseModel):
	email: EmailStr
	username: str
	password: str
	full_name: str
	institution: Optional[str] = None
	research_interests: Optional[List[str]] = None

class UserLogin(BaseModel):
	email_or_username: str
	password: str
	remember_me: bool = False

class PasswordReset(BaseModel):
	email: EmailStr

class PasswordChange(BaseModel):
	current_password: str
	new_password: str

class TwoFactorSetup(BaseModel):
	user_id: str

class TwoFactorVerification(BaseModel):
	code: str
	enable_2fa: bool = False

class APIKeyCreate(BaseModel):
	name: str
	scopes: List[str]
	expires_in_days: Optional[int] = None

class UserProfileUpdate(BaseModel):
	full_name: Optional[str] = None
	bio: Optional[str] = None
	institution: Optional[str] = None
	research_interests: Optional[List[str]] = None
	avatar_url: Optional[str] = None

@router.post("/register")
async def register_user(
	user_data: UserRegistration,
	request: Request,
	background_tasks: BackgroundTasks,
	db_session: AsyncSession = Depends(get_db_session)
):
	client_ip = request.client.host if request.client else "unknown"
	if not await rate_limiter.check_rate_limit(f"register:{client_ip}", max_attempts=5, window_minutes=60):
		raise HTTPException(
			status_code=status.HTTP_429_TOO_MANY_REQUESTS,
			detail="Too many registration attempts. Please try again later."
		)
	auth_service = AuthenticationService(db_session)
	result = await auth_service.register_user(
		email=user_data.email,
		username=user_data.username,
		password=user_data.password,
		full_name=user_data.full_name,
		institution=user_data.institution
	)
	return {
		"success": True,
		"message": "User registered successfully",
		"user": result["user"],
		"auth_token": result["auth_token"],
		"timestamp": "2025-05-27 19:54:25"
	}

@router.post("/login")
async def login_user(
	login_data: UserLogin,
	request: Request,
	db_session: AsyncSession = Depends(get_db_session)
):
	client_ip = request.client.host if request.client else "unknown"
	if not await rate_limiter.check_rate_limit(f"login:{client_ip}", max_attempts=10, window_minutes=15):
		raise HTTPException(
			status_code=status.HTTP_429_TOO_MANY_REQUESTS,
			detail="Too many login attempts. Please try again later."
		)
	auth_service = AuthenticationService(db_session)
	result = await auth_service.login_user(
		email_or_username=login_data.email_or_username,
		password=login_data.password,
		remember_me=login_data.remember_me
	)
	return {
		"success": True,
		"message": "Login successful",
		"user": result["user"],
		"auth_token": result["auth_token"],
		"refresh_token": result["refresh_token"],
		"two_fa_required": result["two_fa_required"],
		"expires_in": result["expires_in"],
		"timestamp": "2025-05-27 19:54:25"
	}

@router.post("/logout")
async def logout_user(
	current_user: UserContext = Depends(get_current_user)
):
	# TODO: Implement JWT token blacklisting for logged out users
	return {
		"success": True,
		"message": f"User {current_user.username} logged out successfully",
		"timestamp": "2025-05-27 19:54:25"
	}

@router.get("/me")
async def get_current_user_profile(
	current_user: UserContext = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session)
):
	return {
		"user": {
			"user_id": current_user.user_id,
			"email": current_user.email,
			"username": current_user.username,
			"full_name": current_user.full_name,
			"is_verified": current_user.is_verified,
			"subscription_tier": current_user.subscription_tier,
			"research_interests": current_user.research_interests,
			"institution": current_user.institution,
			"auth_method": current_user.auth_method
		},
		"timestamp": "2025-05-27 19:54:25"
	}

@router.put("/me")
async def update_user_profile(
	profile_data: UserProfileUpdate,
	current_user: UserContext = Depends(get_verified_user),
	db_session: AsyncSession = Depends(get_db_session)
):
	try:
		from sqlalchemy import select, update
		from app.db.models import UserModel

		update_data = {}
		if profile_data.full_name:
			update_data["full_name"] = profile_data.full_name
		if profile_data.bio:
			update_data["bio"] = profile_data.bio
		if profile_data.institution:
			update_data["institution"] = profile_data.institution
		if profile_data.research_interests:
			update_data["research_interests"] = profile_data.research_interests
		if profile_data.avatar_url:
			update_data["avatar_url"] = profile_data.avatar_url
		
		if update_data:
			update_data["updated_at"] = datetime.utcnow()
			
			await db_session.execute(
				update(UserModel).where(UserModel.user_id == current_user.user_id).values(**update_data)
			)
			await db_session.commit()
		
		return {
			"success": True,
			"message": "Profile updated successfully",
			"updated_fields": list(update_data.keys()),
			"timestamp": "2025-05-27 19:54:25"
		}
	except Exception as e:
		await db_session.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to update profile: {str(e)}"
		)

@router.post("/change-password")
async def change_password(
	password_data: PasswordChange,
	current_user: UserContext = Depends(get_verified_user),
	db_session: AsyncSession = Depends(get_db_session)
):
	try:
		from sqlalchemy import select
		from app.db.models import UserModel
		result = await db_session.execute(
			select(UserModel).where(UserModel.user_id == current_user.user_id)
		)
		user = result.scalar_one_or_none()
		if not user:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="User not found"
			)
		
		if not user.verify_password(password_data.current_password):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Current password is incorrect"
			)
		
		user.set_password(password_data.new_password)
		await db_session.commit()
		return {
			"success": True,
			"message": "Password changed successfully",
			"timestamp": "2025-05-27 19:54:25"
		}
	except HTTPException:
		raise
	except Exception as e:
		await db_session.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to change password: {str(e)}"
		)

@router.post("/2fa/setup")
async def setup_two_factor_auth(
	current_user: UserContext = Depends(get_verified_user),
	db_session: AsyncSession = Depends(get_db_session)
):
	auth_service = AuthenticationService(db_session)
	result = await auth_service.setup_two_factor_auth(current_user.user_id)
	return result

@router.post("/2fa/verify")
async def verify_two_factor_code(
	verification_data: TwoFactorVerification,
	current_user: UserContext = Depends(get_verified_user),
	db_session: AsyncSession = Depends(get_db_session)
):
	auth_service = AuthenticationService(db_session)
	result = await auth_service.verify_two_factor_code(
		user_id=current_user.user_id,
		code=verification_data.code,
		enable_2fa=verification_data.enable_2fa
	)
	return result

@router.post("/api-keys")
async def create_api_key(
	api_key_data: APIKeyCreate,
	current_user: UserContext = Depends(get_verified_user),
	db_session: AsyncSession = Depends(get_db_session)
):
	auth_service = AuthenticationService(db_session)
	result = await auth_service.create_api_key(
		user_id=current_user.user_id,
		name=api_key_data.name,
		scopes=api_key_data.scopes,
		expires_in_days=api_key_data.expires_in_days
	)
	return result

@router.get("/api-keys")
async def list_api_keys(
	current_user: UserContext = Depends(get_verified_user),
	db_session: AsyncSession = Depends(get_db_session)
):
	try:
		from sqlalchemy import select
		from app.db.models import APIKey
		result = await db_session.execute(
			select(APIKey).where(
				APIKey.user_id == current_user.user_id,
				APIKey.is_active == True
			).order_by(APIKey.created_at.desc())
		)
		api_keys = result.scalars().all()
		return {
			"api_keys": [
				{
					"key_id": key.key_id,
					"name": key.name,
					"key_prefix": key.key_prefix,
					"scopes": key.scopes,
					"created_at": key.created_at.isoformat(),
					"last_used": key.last_used.isoformat() if key.last_used else None,
					"expires_at": key.expires_at.isoformat() if key.expires_at else None,
					"total_requests": key.total_requests
				}
				for key in api_keys
			],
			"total_count": len(api_keys),
			"timestamp": "2025-05-27 19:54:25"
		}
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to list API keys: {str(e)}"
		)

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
	key_id: str,
	current_user: UserContext = Depends(get_verified_user),
	db_session: AsyncSession = Depends(get_db_session)
):
	try:
		from sqlalchemy import select, update
		from app.db.models import APIKey
		result = await db_session.execute(
			select(APIKey).where(
				APIKey.key_id == key_id,
				APIKey.user_id == current_user.user_id
			)
		)
		api_key = result.scalar_one_or_none()
		if not api_key:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="API key not found"
			)

		await db_session.execute(
			update(APIKey).where(APIKey.key_id == key_id).values(is_active=False)
		)
		await db_session.commit()
		return {
			"success": True,
			"message": f"API key '{api_key.name}' revoked successfully",
			"timestamp": "2025-05-27 19:54:25"
		}
	except HTTPException:
		raise
	except Exception as e:
		await db_session.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to revoke API key: {str(e)}"
		)

@router.get("/sessions")
async def get_user_research_sessions(
	current_user: UserContext = Depends(get_current_user),
	page: int = 1,
	limit: int = 20,
	db_session: AsyncSession = Depends(get_db_session)
):
	try:
		from sqlalchemy import select, func
		from app.db.models import ResearchSession

		offset = (page - 1) * limit
		result = await db_session.execute(
			select(ResearchSession).where(
				ResearchSession.user_id == current_user.user_id
			).order_by(ResearchSession.created_at.desc()).offset(offset).limit(limit)
		)
		sessions = result.scalars().all()
		count_result = await db_session.execute(
			select(func.count(ResearchSession.session_id)).where(
				ResearchSession.user_id == current_user.user_id
			)
		)
		total_count = count_result.scalar()
		
		return {
			"sessions": [
				{
					"session_id": session.session_id,
					"title": session.title,
					"query": session.query,
					"research_type": session.research_type,
					"status": session.status,
					"progress": session.progress,
					"is_collaborative": session.is_collaborative,
					"visibility": session.visibility,
					"created_at": session.created_at.isoformat(),
					"updated_at": session.updated_at.isoformat(),
					"completed_at": session.completed_at.isoformat() if session.completed_at else None
				}
				for session in sessions
			],
			"pagination": {
				"page": page,
				"limit": limit,
				"total_count": total_count,
				"total_pages": (total_count + limit - 1) // limit
			},
			"timestamp": "2025-05-27 19:54:25"
		}
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get research sessions: {str(e)}")
	
@router.post("/verify-email")
async def verify_email(token: str, db_session: AsyncSession = Depends(get_db_session)):
	try:
		import jwt
		from sqlalchemy import select, update
		from app.db.models import UserModel
		from app.core.config import settings

		try:
			payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
			user_id = payload.get("user_id")
			email = payload.get("email")
			if payload.get("sub") != "email_verification":
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")
		except jwt.ExpiredSignatureError:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token has expired")
		except jwt.InvalidTokenError:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")

		result = await db_session.execute(
			select(UserModel).where(UserModel.user_id == user_id, UserModel.email == email)
		)
		user = result.scalar_one_or_none()
		if not user:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="User not found"
			)
		if user.is_verified:
			return {
				"success": True,
				"message": "Email already verified",
				"timestamp": "2025-05-28 16:47:24"
			}
		await db_session.execute(
			update(UserModel).where(UserModel.user_id == user_id).values(
				is_verified=True,
				email_verified_at=datetime.utcnow()
			)
		)
		await db_session.commit()
		return {
			"success": True,
			"message": "Email verified successfully",
			"timestamp": "2025-05-28 16:47:24"
		}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Email verification failed: {str(e)}")
	
@router.post("/resend-verification")
async def resend_verification_email(current_user: UserContext = Depends(get_current_user), db_session: AsyncSession = Depends(get_db_session)):
	if current_user.is_verified:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already verified")
	
	try:
		from sqlalchemy import select
		from app.db.models import UserModel
		result = await db_session.execute(
			select(UserModel).where(UserModel.user_id == current_user.user_id)
		)
		user = result.scalar_one_or_none()
		if not user:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="User not found"
			)
		auth_service = AuthenticationService(db_session)
		await auth_service._send_verification_email(user)
		return {
			"success": True,
			"message": "Verification email sent successfully",
			"timestamp": "2025-05-28 16:47:24"
		}
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to resend verification email: {str(e)}"
		)