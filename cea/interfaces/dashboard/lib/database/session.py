import os
import sys
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import Depends

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from typing_extensions import Annotated

from cea.interfaces.dashboard.lib.database.settings import database_settings
from cea.interfaces.dashboard.lib.logs import logger
from cea.interfaces.dashboard.settings import get_settings


def get_default_db_directory():
    """Get platform-specific directory for storing application data"""
    try:
        if sys.platform == 'win32':
            # Windows: %APPDATA%\CityEnergyAnalyst
            app_data = os.environ.get('APPDATA', os.path.expandvars(r"%APPDATA%"))
            return os.path.join(app_data, "CityEnergyAnalyst")
        elif sys.platform == 'darwin':
            # macOS: ~/Library/Application Support/CityEnergyAnalyst
            return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'CityEnergyAnalyst')
        else:
            # Linux/Unix: ~/.local/share/CityEnergyAnalyst
            return os.path.join(os.path.expanduser('~'), '.local', 'share', 'CityEnergyAnalyst')
    except Exception:
        # Fallback to user home directory
        return os.path.join(os.path.expanduser('~'), '.cea')


def get_local_database_path():
    """Get the path to the database file."""
    # Try to get from settings (if available)
    db_dir = database_settings.path

    # Use default location if not configured
    if db_dir is None:
        db_dir = get_default_db_directory()

    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "database.db")


def get_connection_props():
    # Only use local database if local mode
    if get_settings().local:
        return f"sqlite+aiosqlite:///{get_local_database_path()}", {"check_same_thread": False}

    # Use database_url if set (priority)
    # Support postgres for now
    if database_settings.url is not None:
        url = make_url(database_settings.url)

        # Replace psycopg2 with asyncpg for PostgreSQL connections
        if url.drivername.startswith("postgresql"):
            url = url.set(drivername="postgresql+asyncpg")

            # strip out sslmode (asyncpg doesn't accept it)
            url = url.set(query={k: v for k, v in url.query.items() if k.lower() != "sslmode"})
            return url.render_as_string(hide_password=False), {}

        return database_settings.url, {}

    raise ValueError("Could not determine database properties")


@lru_cache
def get_engine():
    """
    Create and cache a SQLAlchemy engine per-process.
    Using lru_cache ensures each worker process gets its own engine instance.
    """
    db_url, connect_args = get_connection_props()
    
    # Customize the pool settings for PostgreSQL with asyncpg
    if db_url.startswith("postgresql+asyncpg"):
        # These pool settings work better with multiple uvicorn workers
        return create_async_engine(
            db_url,
            connect_args=connect_args,
            pool_size=5,              # Limit connections per worker
            max_overflow=10,          # Allow some overflow connections
            pool_timeout=30,          # Timeout for getting a connection from pool
            pool_recycle=1800,        # Recycle connections every 30 minutes
            pool_pre_ping=True,       # Check connection validity before using it
        )
    else:
        # For SQLite or other databases, use default settings
        return create_async_engine(db_url, connect_args=connect_args)


# Create a session factory function rather than a global session
def get_async_session_maker():
    """
    Create a session factory for the current process.

    Uses expire_on_commit=True (SQLAlchemy default) which:
    - Expires all objects after commit (attributes become stale)
    - Prevents memory leaks by not holding loaded objects indefinitely
    - Ensures data freshness in multi-worker environments
    - Requires explicit refresh() before accessing expired objects
    """
    engine = get_engine()
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=True)


async def get_session():
    """FastAPI dependency for getting a session"""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context():
    """Async context manager for database sessions."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection():
    """Close the database engine connection pool on application shutdown."""
    logger.info("Closing database connection pool...")
    # If the engine exists in this process, dispose it
    engine = get_engine()
    if engine:
        await engine.dispose()


SessionDep = Annotated[AsyncSession, Depends(get_session)]
