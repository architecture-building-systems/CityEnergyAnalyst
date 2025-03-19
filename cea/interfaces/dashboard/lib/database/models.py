from datetime import datetime, timezone
from enum import IntEnum
import os
from typing import Optional
import uuid

from pydantic import AwareDatetime, computed_field
from sqlmodel import Field, SQLModel, JSON, DateTime

import cea.scripts
from cea.interfaces.dashboard.settings import get_settings

LOCAL_USER_ID = "localuser"
user_table_name = get_settings().user_table_name
user_table_schema = get_settings().user_table_schema


def get_current_time() -> AwareDatetime:
    """Get the current time in UTC"""
    return datetime.now(timezone.utc)


class JobState(IntEnum):
    # Job states
    PENDING = 0
    STARTED = 1
    SUCCESS = 2
    ERROR = 3
    CANCELED = 4
    DELETED = 5


class User(SQLModel, table=True):
    __tablename__ = user_table_name
    __table_args__ = {'schema': user_table_schema}

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)


class Config(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    config: dict = Field(sa_type=JSON, nullable=False)
    user_id: str = Field(foreign_key=f"{user_table_schema}.{user_table_name}.id")


class Project(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    uri: str
    owner: str = Field(foreign_key=f"{user_table_schema}.{user_table_name}.id")


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
    def duration(self) -> Optional[float]:
        """Calculate job execution time in seconds if available"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
