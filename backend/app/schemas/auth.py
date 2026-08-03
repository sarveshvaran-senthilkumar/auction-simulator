import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{2,20}$")


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        v = v.strip()
        if not USERNAME_RE.match(v):
            raise ValueError("2-20 characters, letters/numbers/underscore/dot only")
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    # Accepts either a username or an email, so people don't have to remember which.
    identifier: str
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: str
    display_name: str
    username: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    is_guest: bool = False


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
