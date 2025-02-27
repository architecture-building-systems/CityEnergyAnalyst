from datetime import datetime, timezone
from enum import IntEnum
import os
from typing import Optional
import uuid

from pydantic import computed_field
from sqlmodel import Field, SQLModel, Column, JSON

import cea.scripts

class JobState(IntEnum):
    # Job states
    PENDING = 0
    STARTED = 1
    SUCCESS = 2
    ERROR = 3
    CANCELED = 4


class Project(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    uri: str


class JobInfo(SQLModel, table=True):
    """Store all the information required to run a job"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    script: str = Field(index=True)
    parameters: dict = Field(sa_column=Column(JSON))
    state: JobState = Field(default=JobState.PENDING, index=True)
    error: Optional[str] = None
    created_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    project_id: str = Field(foreign_key="project.id")

    @computed_field
    def script_label(self) -> Optional[str]:
        """Extract the scenario name from parameters if available"""
        script = cea.scripts.by_name(self.script)
        return script.label

    @computed_field
    def scenario_name(self) -> Optional[str]:
        """Extract the scenario name from parameters if available"""
        if self.parameters and "scenario" in self.parameters:
            # TODO: handle scenario name if not a file path
            return os.path.basename(self.parameters["scenario"])
        return None

    @computed_field
    def execution_time(self) -> Optional[float]:
        """Calculate job execution time in seconds if available"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None