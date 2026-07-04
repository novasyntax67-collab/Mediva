from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/healthcare")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Clean query parameters for asyncpg compatibility (e.g. remove pgbouncer)
if "?" in DATABASE_URL:
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    url_parts = list(urlparse(DATABASE_URL))
    query = dict(parse_qsl(url_parts[4]))
    query.pop('pgbouncer', None)
    url_parts[4] = urlencode(query)
    DATABASE_URL = urlunparse(url_parts)

engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db_session():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
