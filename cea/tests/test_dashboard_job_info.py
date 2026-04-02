from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import undefer_group
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from unittest.mock import AsyncMock

from cea.interfaces.dashboard.lib.cache.base import AsyncDictCache
from cea.interfaces.dashboard.lib.database.models import JobInfo, JobState, Project, User
from cea.interfaces.dashboard.server import jobs

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=True)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Pre-populate with a user and project for testing
    async with session_maker() as session:
        session.add(User(id="localuser"))
        session.add(Project(id="project", uri="test", owner="localuser"))
        await session.commit()

    yield session_maker

    await engine.dispose()


class DummyStreams(AsyncDictCache):
    def __init__(self, stream_output):
        self.stream_output = stream_output

    async def pop(self, item_id, default=None):
        if self.stream_output is None:
            return default
        return self.stream_output


class DummyWorkerProcesses(AsyncDictCache):
    def __init__(self):
        pass

    async def pop(self, item_id, default=None):
        return default

    async def delete(self, item_id):
        raise KeyError(item_id)


@pytest.mark.anyio
async def test_set_job_error_serialises_deferred_logs_without_lazy_loading(monkeypatch, db_session):
    async with db_session() as session:
        job = JobInfo(script="radiation-crax", parameters={}, project_id="project", created_by="localuser")
        job_id = job.id
        session.add(job)
        await session.commit()

    monkeypatch.setattr(jobs, "emit_with_retry", AsyncMock(return_value=True))

    async with db_session() as session:
        response = await jobs.set_job_error(
            session,
            job_id,
            jobs.JobError(message="mesh failed", stacktrace="traceback"),
            DummyStreams(["stdout line"]),
            DummyWorkerProcesses(),
        )

        assert response.state == JobState.ERROR
        assert response.error == "mesh failed"
        assert response.stdout == "stdout line"
        assert response.stderr == "traceback"

    async with db_session() as session:
        stored_job = await session.get(JobInfo, job_id, options=[undefer_group("logs")])
        assert stored_job is not None
        assert stored_job.state == JobState.ERROR
        assert stored_job.error == "mesh failed"
        assert stored_job.stdout == "stdout line"
        assert stored_job.stderr == "traceback"


@pytest.mark.anyio
async def test_set_job_success_keeps_datetime_fields_for_response_serialisation(monkeypatch, db_session):
    async with db_session() as session:
        job = JobInfo(
            script="radiation-crax",
            parameters={},
            project_id="project",
            created_by="localuser",
            state=JobState.STARTED,
            start_time=datetime.now(timezone.utc),
        )
        job_id = job.id
        session.add(job)
        await session.commit()

    monkeypatch.setattr(jobs, "emit_with_retry", AsyncMock(return_value=True))

    async with db_session() as session:
        response = await jobs.set_job_success(
            session,
            job_id,
            DummyStreams(["stdout line"]),
            DummyWorkerProcesses(),
            jobs.JobOutput(output={"status": "ok"}),
        )

        assert isinstance(response.start_time, datetime)
        assert isinstance(response.end_time, datetime)

        duration = response.end_time - response.start_time
        assert duration.total_seconds() >= 0
