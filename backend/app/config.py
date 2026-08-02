from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"
DEFAULT_SQLITE_PATH = BACKEND_ROOT / "auction.db"


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "IPL Auction Simulator"
    # Wide-open in dev so the app can be opened from a phone on the same LAN
    # (the origin is then http://<your-lan-ip>:5173, which we can't know upfront).
    CORS_ORIGINS: List[str] = ["*"]

    # Database — SQLite by default so the app runs with zero setup.
    # Point DATABASE_URL at postgresql+asyncpg://... to switch back.
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

    # Auction rules
    DEFAULT_PURSE_LAKH: int = 12000
    BID_TIMER_SECONDS: int = 12       # opening window on a fresh lot
    BID_RESET_SECONDS: int = 7        # shorter window after each bid, so lots keep moving
    MAX_LOT_SECONDS: int = 75         # hard stop: two rich teams can trade bids forever
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
