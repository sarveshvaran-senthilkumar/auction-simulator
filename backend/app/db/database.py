from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from ..config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# SQLite's aiosqlite driver uses a NullPool-style connection model, so the
# server-side pool tuning below only applies to Postgres.
_engine_kwargs = {"echo": False, "future": True}
if not _is_sqlite:
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
