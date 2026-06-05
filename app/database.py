from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
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

