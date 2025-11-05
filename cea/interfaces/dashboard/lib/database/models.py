import os
import uuid
from datetime import datetime, timezone
from enum import IntEnum
from typing import Optional

from pydantic import AwareDatetime, computed_field
from sqlmodel import Field, SQLModel, JSON, DateTime, BigInteger, select, inspect, text

import cea.scripts
from cea.interfaces.dashboard.lib.database.session import (get_engine, get_session_context, get_connection_props,
                                                           database_settings)
from cea.interfaces.dashboard.lib.logs import logger
from cea.interfaces.dashboard.settings import get_settings


def determine_db_type():
    """
    Determine the database type from the database URL.
    Currently local will be sqlite and remote will be postgres.
    Handles driver suffixes like postgresql+asyncpg or postgresql+psycopg2.
    """
    db_url, _ = get_connection_props()

    # Extract scheme (e.g., "postgresql+asyncpg" or "sqlite")
    scheme = db_url.split("://")[0] if "://" in db_url else db_url.split(":")[0]

    # Strip driver suffix (e.g., "postgresql+asyncpg" -> "postgresql")
    return scheme.split("+")[0]


LOCAL_USER_ID = "localuser"

user_table_name = database_settings.user_table_name
user_table_schema = database_settings.user_table_schema
db_type = determine_db_type()

# Include schema name when using postgres
user_table_ref = f"{user_table_schema}.{user_table_name}" if db_type == "postgresql" else user_table_name
table_args = {'schema': user_table_schema} if db_type == "postgresql" else {}


def get_current_time() -> AwareDatetime:
    """Get the current time in UTC"""
    return datetime.now(timezone.utc)


class JobState(IntEnum):
    """
    Job execution states.
    """
    PENDING = 0
    STARTED = 1
    SUCCESS = 2
    ERROR = 3
    CANCELED = 4  # User-initiated cancellation
    KILLED = 5    # Server-initiated termination (e.g., server shutdown)


class DownloadState(IntEnum):
    """
    Download preparation states.
    """
    PENDING = 0      # Download request created, not yet started
    PREPARING = 1    # Currently preparing zip file
    READY = 2        # Zip file ready for download
    DOWNLOADING = 3  # Currently being downloaded (prevents concurrent access)
    ERROR = 4        # Error during preparation
    DOWNLOADED = 5   # File has been downloaded and cleaned up


class User(SQLModel, table=True):
    __tablename__ = user_table_name
    __table_args__ = table_args

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)


class Config(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    config: dict = Field(sa_type=JSON, nullable=False)
    user_id: str = Field(foreign_key=f"{user_table_ref}.id", index=True)


class Project(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    uri: str = Field(nullable=False, index=True)
    owner: str = Field(foreign_key=f"{user_table_ref}.id", index=True)


class JobInfo(SQLModel, table=True):
    __tablename__ = "job"

    """Store all the information required to run a job"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    script: str = Field(index=True)
    parameters: dict = Field(sa_type=JSON)
    state: JobState = Field(default=JobState.PENDING, index=True)
    error: Optional[str] = None
    created_time: AwareDatetime = Field(sa_type=DateTime(timezone=True), nullable=False,
                                        default_factory=get_current_time)
    start_time: Optional[AwareDatetime] = Field(sa_type=DateTime(timezone=True), nullable=True, default=None)
    end_time: Optional[AwareDatetime] = Field(sa_type=DateTime(timezone=True), nullable=True, default=None)
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    project_id: str = Field(foreign_key="project.id", index=True)
    created_by: str = Field(foreign_key=f"{user_table_ref}.id", index=True)
    deleted_at: Optional[AwareDatetime] = Field(sa_type=DateTime(timezone=True), nullable=True, default=None, index=True)
    deleted_by: Optional[str] = Field(foreign_key=f"{user_table_ref}.id", nullable=True, default=None)

    @computed_field
    def script_label(self) -> Optional[str]:
        """Extract the script label from parameters if available in scripts.yml"""
        try:
            script = cea.scripts.by_name(self.script)
            return script.label
        except cea.ScriptNotFoundException as e:
            logger.error(f"Error extracting script label: {e}. Ensure that it is defined in scripts.yml")
            return None

    @computed_field
    def scenario_name(self) -> Optional[str]:
        """Extract the scenario name from parameters if available"""
        if self.parameters and "scenario" in self.parameters:
            # TODO: handle scenario name if not a file path
            return os.path.basename(self.parameters["scenario"])
        return None

    @computed_field
    def duration(self) -> Optional[float]:
        """Calculate job execution time in seconds if available"""
        if self.start_time is not None and self.end_time is not None:
            return (self.end_time - self.start_time).total_seconds()
        return None


class Download(SQLModel, table=True):
    """Store information for scenario download requests"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    scenarios: list[str] = Field(sa_type=JSON)  # List of scenario names
    input_files: bool = Field(default=False)  # Include input files?
    output_files: list[str] = Field(sa_type=JSON)  # List of output types: SUMMARY, DETAILED, EXPORT
    state: DownloadState = Field(default=DownloadState.PENDING, index=True)
    file_path: Optional[str] = None  # Path to prepared zip file
    file_size: Optional[int] = Field(sa_type=BigInteger, nullable=True, default=None)  # Size in bytes
    error_message: Optional[str] = None  # Error details if state=ERROR
    progress_message: Optional[str] = None  # Current progress for UI display
    created_at: AwareDatetime = Field(sa_type=DateTime(timezone=True), nullable=False,
                                      default_factory=get_current_time, index=True)
    downloaded_at: Optional[AwareDatetime] = Field(sa_type=DateTime(timezone=True), nullable=True, default=None)
    created_by: str = Field(foreign_key=f"{user_table_ref}.id", index=True)

    @computed_field
    def file_size_mb(self) -> Optional[float]:
        """Return file size in megabytes for UI display"""
        if self.file_size is not None:
            return round(self.file_size / (1024 * 1024), 2)
        return None

    @computed_field
    def preparation_duration(self) -> Optional[float]:
        """Calculate download preparation time in seconds if available"""
        if self.state in [DownloadState.READY, DownloadState.DOWNLOADED]:
            # Find the time when it became READY (we'll track this separately in implementation)
            # For now, estimate from created_at to when file_path was set
            # This will be refined when we track state transitions
            return None
        return None


async def initialize_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def ensure_local_user():
    """
    Create default local user for development mode.
    Only runs in local mode - production uses external auth (e.g., Neon DB).
    """
    settings = get_settings()
    if not settings.local:
        logger.debug("Skipping local user creation (not in local mode)")
        return

    logger.info("Checking for local user...")
    async with get_session_context() as session:
        result = await session.execute(select(User).where(User.id == LOCAL_USER_ID))
        user = result.scalar()
        if user is None:
            logger.info(f"Creating default local user: {LOCAL_USER_ID}")
            user = User(id=LOCAL_USER_ID)
            session.add(user)
            await session.commit()
        else:
            logger.debug(f"Local user already exists: {LOCAL_USER_ID}")

async def create_db_and_tables():
    """Initialize database tables and run migrations if needed"""
    if not database_settings.init_tables:
        logger.debug("Skipping database initialization")
        return

    logger.info("Preparing database...")
    await initialize_db()
    await migrate_db()
    await ensure_local_user()

async def migrate_db():
    # TODO: Remove once in release new version
    # Check and update existing table schemas
    engine = get_engine()
    async with engine.connect() as conn:        
        # Get table names
        table_names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
        
        # For project table and owner column
        if 'project' in table_names:
            columns = await conn.run_sync(lambda sync_conn: [col['name'] for col in inspect(sync_conn).get_columns('project')])
            if 'owner' not in columns:
                logger.info("Adding 'owner' column to project table...")
                if db_type == "postgresql":
                    await conn.execute(text(f"ALTER TABLE project ADD COLUMN owner VARCHAR REFERENCES {user_table_ref}(id)"))
                else:  # SQLite
                    # SQLite doesn't support adding foreign keys via ALTER TABLE
                    # Foreign key will be enforced on fresh installs via SQLModel
                    await conn.execute(text("ALTER TABLE project ADD COLUMN owner VARCHAR"))
                await conn.commit()
                logger.info("Successfully added 'owner' column")

        if 'job' in table_names:
            columns = await conn.run_sync(lambda sync_conn: [col['name'] for col in inspect(sync_conn).get_columns('job')])
            if 'created_by' not in columns:
                logger.info("Adding 'created_by' column to job table...")
                if db_type == "postgresql":
                    await conn.execute(text(f"ALTER TABLE job ADD COLUMN created_by VARCHAR REFERENCES {user_table_ref}(id)"))
                else:  # SQLite
                    # SQLite doesn't support adding foreign keys via ALTER TABLE
                    # Foreign key will be enforced on fresh installs via SQLModel
                    await conn.execute(text("ALTER TABLE job ADD COLUMN created_by VARCHAR"))
                await conn.commit()
                logger.info("Successfully added 'created_by' column")

            # Add deleted_at column for soft delete functionality
            if 'deleted_at' not in columns:
                logger.info("Adding 'deleted_at' column to job table...")
                if db_type == "postgresql":
                    await conn.execute(text("ALTER TABLE job ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE"))
                else:  # SQLite
                    await conn.execute(text("ALTER TABLE job ADD COLUMN deleted_at DATETIME"))
                await conn.commit()
                logger.info("Successfully added 'deleted_at' column")

            # Add deleted_by column to track who deleted the job
            if 'deleted_by' not in columns:
                logger.info("Adding 'deleted_by' column to job table...")
                if db_type == "postgresql":
                    await conn.execute(text(f"ALTER TABLE job ADD COLUMN deleted_by VARCHAR REFERENCES {user_table_ref}(id)"))
                else:  # SQLite
                    # SQLite doesn't support adding foreign keys via ALTER TABLE
                    # Foreign key will be enforced on fresh installs via SQLModel
                    await conn.execute(text("ALTER TABLE job ADD COLUMN deleted_by VARCHAR"))
                await conn.commit()
                logger.info("Successfully added 'deleted_by' column")
