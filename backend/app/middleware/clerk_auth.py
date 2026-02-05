"""
Clerk JWT Authentication Middleware for FastAPI
Validates JWT tokens issued by Clerk
"""
import jwt
import httpx
from typing import Optional
from functools import lru_cache
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.core.config import get_settings


class ClerkUser(BaseModel):
    """Represents an authenticated Clerk user"""
    user_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    image_url: Optional[str] = None


class ClerkJWKS:
    """Clerk JWKS (JSON Web Key Set) handler"""

    def __init__(self):
        self._jwks: Optional[dict] = None
        self._jwks_client: Optional[jwt.PyJWKClient] = None

    def get_jwks_client(self) -> jwt.PyJWKClient:
        """Get or create JWKS client"""
        if self._jwks_client is None:
            settings = get_settings()
            jwks_url = f"{settings.clerk_jwt_issuer}/.well-known/jwks.json"
            self._jwks_client = jwt.PyJWKClient(jwks_url)
        return self._jwks_client


# Singleton JWKS handler
_clerk_jwks = ClerkJWKS()


security = HTTPBearer(auto_error=False)


async def verify_clerk_token(token: str) -> Optional[ClerkUser]:
    """
    Verify a Clerk JWT token and extract user information

    Args:
        token: JWT token from Authorization header

    Returns:
        ClerkUser if valid, None otherwise
    """
    settings = get_settings()

    try:
        # Get signing key from JWKS
        jwks_client = _clerk_jwks.get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_jwt_issuer,
            options={
                "verify_aud": False,  # Clerk doesn't always include aud
                "verify_exp": True,
                "verify_iss": True,
            }
        )

        # Extract user info from Clerk token claims
        user_id = payload.get("sub")
        if not user_id:
            return None

        return ClerkUser(
            user_id=user_id,
            email=payload.get("email"),
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            image_url=payload.get("image_url"),
        )

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[ClerkUser]:
    """
    Dependency to get the current authenticated user (optional)
    Returns None if not authenticated
    """
    if credentials is None:
        return None

    user = await verify_clerk_token(credentials.credentials)
    return user


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> ClerkUser:
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

    user = await verify_clerk_token(credentials.credentials)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


class ClerkAuthMiddleware:
    """
    ASGI Middleware for Clerk authentication
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
                user = await verify_clerk_token(token)

            # Add user to scope state
            scope["state"] = scope.get("state", {})
            scope["state"]["user"] = user

        await self.app(scope, receive, send)
