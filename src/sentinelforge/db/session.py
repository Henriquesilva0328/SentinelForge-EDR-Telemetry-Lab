from collections.abc import AsyncGenerator
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sentinelforge.core.settings import get_settings

settings = get_settings()

# pool_pre_ping ajuda a detectar conexões mortas em uso.
engine = create_async_engine(
    settings.db_url,
    pool_pre_ping=True,
)

SessionFactory = async_sessionmaker(
    bind=engine,
    class_= AsyncSession,
    expire_on_commit= False,
    autoflush=False,
)

async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session