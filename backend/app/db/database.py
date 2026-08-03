from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from ..config import settings


def async_url(url: str) -> str:
    """Force a URL onto an async driver.

    Hosting providers hand out plain `postgres://` / `postgresql://` strings,
    but SQLAlchemy's async engine needs an async DBAPI spelled out. Rewriting it
    here means you can paste a provider's connection string straight into
    DATABASE_URL without editing it.
    """
    if url.startswith("postgres://"):  # Heroku-style alias
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("sqlite://"):
        return "sqlite+aiosqlite://" + url[len("sqlite://"):]
    return url


DATABASE_URL = async_url(settings.DATABASE_URL)
_is_sqlite = DATABASE_URL.startswith("sqlite")

# SQLite's aiosqlite driver uses a NullPool-style connection model, so the
# server-side pool tuning below only applies to Postgres.
_engine_kwargs = {"echo": False, "future": True}
if not _is_sqlite:
    # Keep the pool modest: hosted Postgres plans cap total connections, and
    # this app runs as a single instance anyway.
    _engine_kwargs.update(pool_size=5, max_overflow=10, pool_pre_ping=True)

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

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
