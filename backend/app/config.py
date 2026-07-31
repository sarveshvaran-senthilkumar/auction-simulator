from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "IPL Auction Simulator"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ipl_auction"
    MONGODB_URI: str = "mongodb://localhost:27017"
    
    # Auction Rules
    DEFAULT_PURSE_LAKH: int = 12000
    BID_TIMER_SECONDS: int = 15
    MIN_BID_INCREMENT_LAKH: int = 25
    MAX_SQUAD_SIZE: int = 25
    MAX_OVERSEAS: int = 8
    RETENTION_TIMEOUT_SECONDS: int = 120

    class Config:
        env_file = ".env"

settings = Settings()
