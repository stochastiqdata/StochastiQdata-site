"""
Supabase JWT Authentication Middleware for FastAPI
Validates JWT tokens issued by Supabase Auth
"""
import jwt
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.core.config import get_settings


class SupabaseUser(BaseModel):
    """Represents an authenticated Supabase user"""
    user_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


security = HTTPBearer(auto_error=False)


def get_jwt_secret() -> str:
    """Get the JWT secret from Supabase settings"""
    settings = get_settings()
    # Supabase uses the service key as JWT secret for verification
    # The anon key can also be used for public tokens
    return settings.supabase_jwt_secret


async def verify_supabase_token(token: str) -> Optional[SupabaseUser]:
    """
    Verify a Supabase JWT token and extract user information

    Args:
        token: JWT token from Authorization header

    Returns:
        SupabaseUser if valid, None otherwise
    """
    settings = get_settings()

    try:
        # Decode and verify token
        # Supabase tokens are signed with HS256 using the JWT secret
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={
                "verify_exp": True,
                "verify_aud": True,
            }
        )

        # Extract user info from Supabase token claims
        user_id = payload.get("sub")
        if not user_id:
            return None

        # User metadata is stored in user_metadata claim
        user_metadata = payload.get("user_metadata", {})

        return SupabaseUser(
            user_id=user_id,
            email=payload.get("email"),
            first_name=user_metadata.get("first_name"),
            last_name=user_metadata.get("last_name"),
            full_name=user_metadata.get("full_name") or user_metadata.get("name"),
            avatar_url=user_metadata.get("avatar_url") or user_metadata.get("picture"),
        )

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[SupabaseUser]:
    """
    Dependency to get the current authenticated user (optional)
    Returns None if not authenticated
    """
    if credentials is None:
        return None

    user = await verify_supabase_token(credentials.credentials)
    return user


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> SupabaseUser:
    """
    Dependency that requires authentication
    Raises 401 if not authenticated
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await verify_supabase_token(credentials.credentials)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


class SupabaseAuthMiddleware:
    """
    ASGI Middleware for Supabase authentication
    Adds user info to request state if authenticated
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract token from headers
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()

            user = None
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                user = await verify_supabase_token(token)

            # Add user to scope state
            scope["state"] = scope.get("state", {})
            scope["state"]["user"] = user

        await self.app(scope, receive, send)
