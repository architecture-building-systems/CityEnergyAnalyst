from datetime import datetime, timezone
from enum import IntEnum
from typing import Optional

from sqlmodel import Field, SQLModel, Column, JSON

class JobState(IntEnum):
    # Job states
    PENDING = 0
    STARTED = 1
    SUCCESS = 2
    ERROR = 3
    CANCELED = 4


class JobInfo(SQLModel, table=True):
    """Store all the information required to run a job"""
    id: str = Field(default=None, primary_key=True)
    script: str = Field(index=True)
    parameters: dict = Field(sa_column=Column(JSON))
    state: JobState = Field(default=JobState.PENDING, index=True)
    error: Optional[str] = None
    created_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
