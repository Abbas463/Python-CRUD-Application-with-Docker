from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

#class Base(DeclarativeBase):

engine = create_async_engine(
    settings.databaseurl,
    echo=settings.DB_ECHO,
    pool_size=5,
    max_overflow=10
    pool_timeout=30,
    pool_recycle=1800,
    pool_prePping=True
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=True,
    expire_on_commit=False
)

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionFactory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def init_db() ->None:
    from app import models

    async with engine.begin() as connection:
        await connection.run_sync(Base.metada.create_All())

