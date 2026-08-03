"""Password hashing, session tokens, and Google ID-token verification."""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..config import settings
from ..db.database import get_db
from ..db.models import User

GOOGLE_TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"
# bcrypt refuses anything over 72 bytes rather than silently truncating.
MAX_PASSWORD_BYTES = 72


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode()[:MAX_PASSWORD_BYTES], bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: Optional[str]) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode()[:MAX_PASSWORD_BYTES], hashed.encode())
    except ValueError:
        return False


def create_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(days=settings.TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def verify_google_token(id_token: str) -> dict:
    """Validate a Google ID token and return its claims.

    Uses Google's tokeninfo endpoint rather than local signature checking: it
    keeps the dependency list to zero extra packages, and this app's login rate
    is nowhere near where that trade-off would matter.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(503, "Google sign-in is not configured on this server")

    url = f"{GOOGLE_TOKENINFO}?{urllib.parse.urlencode({'id_token': id_token})}"
    try:
        with urllib.request.urlopen(url, timeout=10) as res:
            claims = json.load(res)
    except Exception:
        raise HTTPException(401, "Could not verify that Google sign-in")

    if claims.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(401, "That Google token was issued for another app")
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(401, "Unexpected token issuer")
    if claims.get("email_verified") not in ("true", True):
        raise HTTPException(401, "That Google account has no verified email")

    return claims


def _bearer(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


async def current_user_optional(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """The signed-in user, or None. Used where guests are still welcome."""
    token = _bearer(request)
    if not token:
        return None
    user_id = decode_token(token)
    if not user_id:
        return None
    return (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()


async def current_user(user: Optional[User] = Depends(current_user_optional)) -> User:
    if user is None:
        raise HTTPException(401, "Sign in to continue")
    return user
