from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from ..config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
