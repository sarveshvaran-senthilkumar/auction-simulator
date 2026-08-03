from pathlib import Path
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"
DEFAULT_SQLITE_PATH = BACKEND_ROOT / "auction.db"


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "IPL Auction Simulator"
    # Wide-open in dev so the app can be opened from a phone on the same LAN
    # (the origin is then http://<your-lan-ip>:5173, which we can't know upfront).
    # In production set this to your frontend's URL, e.g.
    #   CORS_ORIGINS=https://my-auction.vercel.app
    # Comma-separated for several.
    CORS_ORIGINS: Union[str, List[str]] = ["*"]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def split_origins(cls, v):
        # Env vars arrive as a plain string; a comma-separated list is far
        # friendlier to type into a hosting dashboard than JSON.
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # Database — SQLite by default so the app runs with zero setup.
    # Point DATABASE_URL at postgresql+asyncpg://... to switch back.
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

    # Auth. Override SECRET_KEY in backend/.env before exposing this beyond
    # your own network — it signs every session token.
    SECRET_KEY: str = "dev-only-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    TOKEN_TTL_DAYS: int = 30
    # From Google Cloud Console -> Credentials -> OAuth 2.0 Client ID (Web).
    # Leave blank and the app simply hides the "Continue with Google" button.
    GOOGLE_CLIENT_ID: str = ""

    # Auction rules
    DEFAULT_PURSE_LAKH: int = 12000
    BID_TIMER_SECONDS: int = 15       # opening window on a fresh lot
    BID_RESET_SECONDS: int = 15       # window after each bid -- your time to counter
    # Hard stop: bids reset the window, so two rich teams can otherwise trade
    # increments forever. Scaled to the 15s window (a hot lot runs ~25 bids).
    MAX_LOT_SECONDS: int = 180
    MIN_BID_INCREMENT_LAKH: int = 25
    MAX_SQUAD_SIZE: int = 25
    MIN_SQUAD_SIZE: int = 18
    MAX_OVERSEAS: int = 8
    RETENTION_TIMEOUT_SECONDS: int = 180
    RTM_DECISION_SECONDS: int = 15

    # AI pacing — how long an AI franchise "thinks" before countering.
    AI_MIN_DELAY_MS: int = 700
    AI_MAX_DELAY_MS: int = 2600

    class Config:
        env_file = ".env"


settings = Settings()
