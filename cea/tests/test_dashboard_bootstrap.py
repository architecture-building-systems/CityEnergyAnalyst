"""Tests for dashboard preparation performed before Uvicorn starts workers."""
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import cea.interfaces.dashboard.bootstrap as bootstrap
import cea.interfaces.dashboard.dashboard as dashboard


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_initialize_dashboard_prepares_shared_state_once(monkeypatch):
    events = []

    async def cleanup_old(session):
        assert session == "session"
        events.append("old-downloads")

    async def cleanup_stale(session):
        assert session == "session"
        events.append("stale-downloads")

    @asynccontextmanager
    async def session_context():
        events.append("session-open")
        yield "session"
        events.append("session-close")

    async def create_tables():
        events.append("database")

    monkeypatch.setattr(bootstrap, "create_db_and_tables", create_tables)
    monkeypatch.setattr(bootstrap, "get_session_context", session_context)
    monkeypatch.setattr(bootstrap, "cleanup_old_downloads", cleanup_old)
    monkeypatch.setattr(bootstrap, "cleanup_stale_downloads", cleanup_stale)
    monkeypatch.setattr(bootstrap, "close_db_connection", AsyncMock())

    await bootstrap.initialize_dashboard()

    assert events == ["database", "session-open", "old-downloads", "stale-downloads", "session-close"]
    bootstrap.close_db_connection.assert_awaited_once()


def test_dashboard_launcher_bootstraps_before_starting_uvicorn(monkeypatch):
    events = []
    settings = Mock(host="127.0.0.1", port=5050, workers=4)
    settings.to_env_vars.side_effect = lambda: events.append("settings-exported")

    async def initialize():
        events.append("bootstrap")

    monkeypatch.setattr(dashboard, "get_settings", lambda: settings)
    monkeypatch.setattr(dashboard, "load_from_config", lambda *_: None)
    monkeypatch.setattr(dashboard, "initialize_dashboard", initialize)
    monkeypatch.setattr(dashboard.uvicorn, "run", lambda *_, **__: events.append("uvicorn"))

    dashboard.main(SimpleNamespace(server=SimpleNamespace(dev=False)))

    assert events == ["settings-exported", "bootstrap", "uvicorn"]
