from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import secrets
import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import pyotp
import qrcode
import io
import base64
from passlib.context import CryptContext

from app.db.models import User, UserPreferences, APIKey
from app.core.config import settings
from app.core.email_service import EmailService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthenticationService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.email_service = EmailService()

    async def register_user(self, email: str, username: str, password: str, full_name: str, institution: Optional[str] = None) -> Dict[str, Any]:
        try:
            existing_user = await self._get_user_by_email_or_username(email, username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email or username already exists"
                )
            
            password_validation = self._validate_password_strength(password)
            if not password_validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password validation failed: {', '.join(password_validation['issues'])}"
                )
            
            user = User(
                email=email.lower(),
                username=username.lower(),
                full_name=full_name,
                institution=institution,
                research_interests=[]
            )
            user.set_password(password)
            self.db_session.add(user)
            await self.db_session.flush()
            preferences = UserPreferences(user_id=user.user_id)
            self.db_session.add(preferences)

            await self.db_session.commit()
            await self._send_verification_email(user)
            auth_token = user.generate_auth_token(settings.SECRET_KEY)
            
            return {
                "success": True,
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at.isoformat()
                },
                "auth_token": auth_token,
                "message": "User registered successfully. Please check your email for verification."
            }
        except HTTPException:
            raise
        except Exception as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )

    async def login_user(
        self, 
        email_or_username: str, 
        password: str,
        remember_me: bool = False
    ) -> Dict[str, Any]:
        try:
            user = await self._get_user_by_email_or_username(email_or_username, email_or_username)
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is deactivated")
            if not user.verify_password(password):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            two_fa_required = user.two_factor_enabled
            user.update_last_login()
            await self.db_session.commit()

            expires_delta = timedelta(days=30) if remember_me else timedelta(hours=24)
            auth_token = user.generate_auth_token(settings.SECRET_KEY, expires_delta)
            refresh_token = self._generate_refresh_token(user.user_id)
            
            return {
                "success": True,
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_verified": user.is_verified,
                    "subscription_tier": user.subscription_tier,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                },
                "auth_token": auth_token,
                "refresh_token": refresh_token,
                "two_fa_required": two_fa_required,
                "expires_in": int(expires_delta.total_seconds())
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if not user_id:
                return None
            
            result = await self.db_session.execute(
                select(User).where(User.user_id == user_id, User.is_active == True)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            return {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "subscription_tier": user.subscription_tier,
                "research_interests": user.research_interests or [],
                "institution": user.institution
            }
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    async def setup_two_factor_auth(self, user_id: str) -> Dict[str, Any]:
        try:
            result = await self.db_session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            secret = pyotp.random_base32()
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name="PerplexiQuest"
            )
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = io.BytesIO()
            qr_image.save(qr_buffer, format="PNG")
            qr_code_b64 = base64.b64encode(qr_buffer.getvalue()).decode()

            user.two_factor_secret = secret
            await self.db_session.commit()

            return {
                "success": True,
                "secret": secret,
                "qr_code": f"data:image/png;base64,{qr_code_b64}",
                "manual_entry_key": secret,
                "message": "Scan the QR code with your authenticator app"
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to setup 2FA: {str(e)}"
            )

    async def verify_two_factor_code(self, user_id: str, code: str, enable_2fa: bool = False) -> Dict[str, Any]:
        try:
            result = await self.db_session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.two_factor_secret:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA not set up for this user"
                )
            totp = pyotp.TOTP(user.two_factor_secret)
            if not totp.verify(code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid authentication code"
                )
            if enable_2fa:
                user.two_factor_enabled = True
                await self.db_session.commit()
            return {
                "success": True,
                "two_fa_enabled": user.two_factor_enabled,
                "message": "Authentication code verified successfully"
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify 2FA code: {str(e)}"
            )

    async def create_api_key(
        self, 
        user_id: str, 
        name: str, 
        scopes: list,
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            api_key = secrets.token_urlsafe(32)
            key_prefix = api_key[:8]
            key_hash = pwd_context.hash(api_key)
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            api_key_record = APIKey(
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                scopes=scopes,
                expires_at=expires_at
            )
            self.db_session.add(api_key_record)
            await self.db_session.commit()
            return {
                "success": True,
                "api_key": api_key,
                "key_id": api_key_record.key_id,
                "name": name,
                "scopes": scopes,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "created_at": api_key_record.created_at.isoformat(),
                "message": "API key created successfully. Store it securely - it won't be shown again."
            }
        except Exception as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create API key: {str(e)}"
            )

    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        try:
            result = await self.db_session.execute(
                select(APIKey).where(
                    APIKey.is_active == True,
                    APIKey.key_prefix == api_key[:8]
                )
            )
            api_keys = result.scalars().all()
            
            valid_key = None
            for key_record in api_keys:
                if pwd_context.verify(api_key, key_record.key_hash):
                    if key_record.expires_at and key_record.expires_at < datetime.now():
                        continue
                    valid_key = key_record
                    break
            
            if not valid_key:
                return None
            valid_key.total_requests += 1
            valid_key.last_used = datetime.now()
            result = await self.db_session.execute(
                select(User).where(User.user_id == valid_key.user_id, User.is_active == True)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            await self.db_session.commit()
            return {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "scopes": valid_key.scopes,
                "rate_limit": valid_key.rate_limit_per_hour,
                "subscription_tier": user.subscription_tier
            }
            
        except Exception:
            return None

    async def _get_user_by_email_or_username(self, email: str, username: str) -> Optional[User]:
        result = await self.db_session.execute(
            select(User).where(
                (User.email == email.lower()) | (User.username == username.lower())
            )
        )
        return result.scalar_one_or_none()

    def _validate_password_strength(self, password: str) -> Dict[str, Any]:
        issues = []
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "strength": "strong" if len(issues) == 0 else "weak"
        }

    def _generate_refresh_token(self, user_id: str) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.now() + timedelta(days=30),
            "iat": datetime.now(),
            "sub": "refresh_token"
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    async def _send_verification_email(self, user: User):
        verification_token = jwt.encode(
            {
                "user_id": user.user_id,
                "email": user.email,
                "exp": datetime.now() + timedelta(hours=24),
                "sub": "email_verification"
            },
            settings.SECRET_KEY,
            algorithm="HS256"
        )
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        await self.email_service.send_verification_email(
            user.email,
            user.full_name,
            verification_url
        )
