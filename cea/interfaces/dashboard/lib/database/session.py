import os
import sys
from contextlib import asynccontextmanager

from fastapi import Depends

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from typing_extensions import Annotated

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
    settings = get_settings()
    db_dir = settings.db_path

    # Use default location if not configured
    if db_dir is None:
        db_dir = get_default_db_directory()

    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "database.db")


def get_connection_props():
    settings = get_settings()

    # Only use local database if local mode
    if get_settings().local:
        return f"sqlite:///{get_local_database_path()}", {"check_same_thread": False}

    # Use database_url if set (priority)
    # Support postgres for now
    if settings.db_url is not None:
        url = make_url(settings.db_url)

        # Replace psycopg2 with asyncpg for PostgreSQL connections
        if url.drivername.startswith("postgresql"):
            url = url.set(drivername="postgresql+asyncpg")

            # strip out sslmode (asyncpg doesn’t accept it)
            q = {k: v for k, v in url.query.items() if k.lower() != "sslmode"}
            url = url._replace(query=q)
            return url.render_as_string(hide_password=False), {}

        return settings.db_url, {}

    raise ValueError("Could not determine database properties")


db_url, connect_args = get_connection_props()
engine = create_async_engine(db_url, connect_args=connect_args)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context():
    """Async context manager for database sessions."""
    async with async_session() as session:
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
    await engine.dispose()


SessionDep = Annotated[AsyncSession, Depends(get_session)]
