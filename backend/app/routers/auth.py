from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..auth.security import (
    create_token,
    current_user,
    hash_password,
    verify_google_token,
    verify_password,
)
from ..config import settings
from ..db.database import get_db
from ..db.models import User
from ..schemas.auth import (
    AuthResponse,
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _as_response(user: User) -> dict:
    return {
        "token": create_token(user.id),
        "user": UserResponse(
            id=user.id,
            display_name=user.display_name,
            username=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            is_guest=bool(user.is_guest),
        ),
    }


async def _find(db: AsyncSession, column, value):
    if value is None:
        return None
    # Case-insensitive so "Sarvesh" and "sarvesh" are the same account.
    return (await db.execute(
        select(User).where(sqlfunc.lower(column) == value.lower())
    )).scalar_one_or_none()


@router.get("/config")
async def auth_config():
    """Lets the app hide the Google button when no client id is configured."""
    return {"google_enabled": bool(settings.GOOGLE_CLIENT_ID),
            "google_client_id": settings.GOOGLE_CLIENT_ID}


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if await _find(db, User.username, req.username):
        raise HTTPException(409, "That username is taken")
    if await _find(db, User.email, req.email):
        raise HTTPException(409, "An account already exists for that email")

    user = User(
        display_name=(req.display_name or req.username).strip(),
        username=req.username,
        email=str(req.email).lower(),
        password_hash=hash_password(req.password),
        is_guest=False,
    )
    db.add(user)
    await db.commit()
    return _as_response(user)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await _find(db, User.username, req.identifier)
    if user is None:
        user = await _find(db, User.email, req.identifier)

    # Same message either way, so this can't be used to enumerate accounts.
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Incorrect username or password")

    user.last_seen_at = datetime.now(timezone.utc)
    await db.commit()
    return _as_response(user)


@router.post("/google", response_model=AuthResponse)
async def google_login(req: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    claims = verify_google_token(req.id_token)
    sub, email = claims.get("sub"), (claims.get("email") or "").lower()

    user = (await db.execute(
        select(User).where(User.google_sub == sub)
    )).scalar_one_or_none()

    # Link Google to an existing password account with the same verified email
    # rather than creating a duplicate.
    if user is None and email:
        user = await _find(db, User.email, email)
        if user is not None:
            user.google_sub = sub

    if user is None:
        user = User(
            display_name=claims.get("name") or email.split("@")[0] or "Manager",
            email=email or None,
            google_sub=sub,
            avatar_url=claims.get("picture"),
            is_guest=False,
        )
        db.add(user)
    else:
        user.is_guest = False
        if not user.avatar_url:
            user.avatar_url = claims.get("picture")

    user.last_seen_at = datetime.now(timezone.utc)
    await db.commit()
    return _as_response(user)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(current_user)):
    return UserResponse(
        id=user.id,
        display_name=user.display_name,
        username=user.username,
        email=user.email,
        avatar_url=user.avatar_url,
        is_guest=bool(user.is_guest),
    )
