from __future__ import annotations

import os
from dataclasses import dataclass

from aiocache import caches, Cache, BaseCache
from aiocache.serializers import PickleSerializer
from fastapi import Depends, Request
from sqlmodel import select
from typing_extensions import Annotated

import cea.config
from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID, Project, Config
from cea.interfaces.dashboard.lib.database.session import SessionDep, get_session_context
from cea.interfaces.dashboard.settings import get_settings
from cea.plots.cache import PlotCache

CACHE_NAME = 'default'
caches.set_config({
    CACHE_NAME: {
        'cache': Cache.MEMORY,
        'serializer': {
            'class': PickleSerializer
        }
    }
})


class AsyncDictCache:
    def __init__(self, cache: BaseCache, cache_key: str):
        self._cache = cache
        self._cache_key = cache_key

    async def get(self, item_id):
        _dict = await self._cache.get(self._cache_key, dict())
        return _dict[item_id]

    async def set(self, item_id, value):
        _dict = await self._cache.get(self._cache_key, dict())
        _dict[item_id] = value
        await self._cache.set(self._cache_key, _dict)

        return value

    async def delete(self, item_id):
        _dict = await self._cache.get(self._cache_key, dict())
        del _dict[item_id]
        await self._cache.set(self._cache_key, _dict)

    async def values(self):
        _dict = await self._cache.get(self._cache_key)
        return _dict.values()

    async def keys(self):
        _dict = await self._cache.get(self._cache_key)
        return _dict.keys()

class CEALocalConfig(cea.config.Configuration):
    def __init__(self, config_file: str = get_settings().config_path):
        if config_file.startswith("~"):
            config_file = os.path.expanduser(config_file)
        super().__init__(config_file)

    def save(self, config_file: str = get_settings().config_path) -> None:
        if config_file.startswith("~"):
            config_file = os.path.expanduser(config_file)
        print(f"Saving config to {config_file}")
        super().save(config_file)


class CEADatabaseConfig(cea.config.Configuration):
    def __init__(self, user_id: str):
        super().__init__(cea.config.DEFAULT_CONFIG)

        self.user_id = user_id
        self.read()

    def from_dict(self, config_dict: dict):
        """
        Create a Configuration object from a dictionary.
        """
        for section_name, section_dict in config_dict.items():
            section = self.sections[section_name]
            for parameter_name, parameter_value in section_dict.items():
                section.parameters[parameter_name].set(parameter_value)
        return self

    def to_dict(self) -> dict:
        """
        Returns the configuration as a dictionary.
        """
        return {
            section.name: {
                parameter.name: self.user_config.get(section.name, parameter.name)
                for parameter in section.parameters.values()
            } for section in self.sections.values()
        }

    def read(self):
        with get_session_context() as session:
            _config = session.exec(select(Config).where(Config.user_id == self.user_id)).first()

            if _config:
                self.from_dict(_config.config)
            else:
                # Create config record if not found
                self.save()

            return self

    def save(self, config_file: str = None) -> None:
        """Saves config to database in dict format"""
        print("Saving config to database")
        with get_session_context() as session:
            session.add(Config(user_id=self.user_id, config=self.to_dict()))
            session.commit()


async def get_cea_config(user_id: CEAUser = None, request: Request = None):
    """Get configuration from request headers or query parameters"""

    # Load config from body (priority)
    # if request and request.method in ["POST", "PUT", "PATCH"]:
    #     try:
    #         body = await request.json()
    #         if "config" in body:
    #             return json.loads(body["config"])
    #     except json.JSONDecodeError:
    #         pass

    if get_settings().db_url is not None:
        return CEADatabaseConfig(user_id)

    # Read config from file if config_path is set
    if get_settings().config_path is not None:
        return CEALocalConfig()

    raise ValueError("No config provided")


@dataclass
class ProjectInfo:
    project: str
    scenario: str


async def get_project_info() -> ProjectInfo:
    """Get the current project and scenario in the config"""
    config = await get_cea_config()
    return ProjectInfo(
        project=config.project,
        scenario=config.scenario,
    )


async def get_project_id(session: SessionDep, owner: CEAUser,
                         project_root: CEAProjectRoot, project_info: CEAProjectInfo):
    """Get the project ID from the project URI."""
    project_uri = project_info.project
    if project_root is not None:
        project_uri = os.path.join(project_root, project_uri)

    project = session.exec(select(Project).where(Project.uri == project_uri)).first()

    # If project not found, create a new one
    if not project:
        project = Project(uri=project_uri, owner=owner)
        session.add(project)
        session.commit()
        session.refresh(project)

    return project.id


async def get_plot_cache():
    cea_config = await get_cea_config()
    _plot_cache = PlotCache(cea_config.project)

    return _plot_cache


async def get_worker_processes():
    _cache = caches.get(CACHE_NAME)
    worker_processes = await _cache.get("worker_processes")

    if worker_processes is None:
        worker_processes = dict()
        await _cache.set("worker_processes", worker_processes)

    return AsyncDictCache(_cache, "worker_processes")


def get_server_url():
    host = get_settings().host
    port = get_settings().port
    worker_url = f"http://{host}:{port}/server"
    return worker_url


def get_project_root():
    return get_settings().project_root


def get_current_user_id():
    if get_settings().local:
        return LOCAL_USER_ID

    # TODO: Get user from request cookie
    raise ValueError("Could not determine current user")


CEAUser = Annotated[str, Depends(get_current_user_id)]
CEAConfig = Annotated[cea.config.Configuration, Depends(get_cea_config)]
CEAProjectInfo = Annotated[ProjectInfo, Depends(get_project_info)]
CEAProjectID = Annotated[str, Depends(get_project_id)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]
CEAWorkerProcesses = Annotated[dict, Depends(get_worker_processes)]
CEAServerUrl = Annotated[str, Depends(get_server_url)]
CEAProjectRoot = Annotated[str, Depends(get_project_root)]
CEAServerSettings = Annotated[dict, Depends(get_settings)]
