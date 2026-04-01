"""
JWT Authentication and Authorization for CreatorConnectAI.

JWT Protection Pattern
----------------------
FastAPI uses dependency injection rather than traditional middleware for JWT validation.

- Protected routes declare `Depends(get_current_user)` in their path-operation signature.
  The dependency decodes and validates the Bearer token, raising HTTP 401 automatically
  for missing, expired, or malformed tokens.

- Public routes (e.g. GET /api/creators/featured) simply omit the dependency — no token
  is required and no 401 is raised.

- `oauth2_scheme` (OAuth2PasswordBearer) handles extraction of the Bearer token from the
  Authorization header. If the header is absent it raises HTTP 401 before the dependency
  body even runs.

Role-based access
-----------------
- `require_business` / `require_creator` are pre-built dependency instances that first
  call `get_current_user` and then assert the role claim, raising HTTP 403 on mismatch.

Usage example::

    @router.get("/api/deals", dependencies=[Depends(require_business)])
    async def list_deals(): ...

    @router.get("/api/creators/featured")   # public — no dependency
    async def featured_creators(): ...

Requirement: Req 1.3 — unauthenticated requests to /api/* return HTTP 401.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError, jwt

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises HTTP 401 on failure."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency that returns the decoded token payload."""
    return decode_access_token(token)


def require_role(role: str):
    """Dependency factory that checks the user's role. Raises HTTP 403 if role doesn't match."""
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to {role} accounts",
            )
        return current_user
    return dependency


require_business = require_role("business")
require_creator = require_role("creator")
