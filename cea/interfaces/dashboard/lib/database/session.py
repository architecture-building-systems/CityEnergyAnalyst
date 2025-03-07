import os
import sys

from fastapi import Depends
from sqlmodel import create_engine, Session, SQLModel

from typing_extensions import Annotated

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

def get_database_path():
    """Get the path to the database file."""
    # Try to get from settings (if available)
    settings = get_settings()
    db_dir = settings.database_path

    # Use default location if not configured
    if db_dir is None:
        db_dir = get_default_db_directory()
    
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "database.db")

sqlite_file_name = get_database_path()
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    print(f"Preparing database at {sqlite_url}")
    SQLModel.metadata.create_all(engine)

SessionDep = Annotated[Session, Depends(get_session)]
