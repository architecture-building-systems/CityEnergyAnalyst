from datetime import datetime
from enum import IntEnum
from typing import Optional

from sqlmodel import Field, SQLModel

class JobState(IntEnum):
    # Job states
    PENDING = 0
    STARTED = 1
    SUCCESS = 2
    ERROR = 3
    CANCELED = 4


class JobInfo(SQLModel, table=True):
    """Store all the information required to run a job"""
    id: Optional[int] = Field(default=None, primary_key=True)
    script: str = Field(index=True)
    parameters: str
    state: JobState = Field(default=JobState.PENDING, index=True)
    error: Optional[str] = None
    start_time: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    end_time: Optional[datetime] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
