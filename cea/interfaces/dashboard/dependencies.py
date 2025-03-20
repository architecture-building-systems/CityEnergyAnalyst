from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass

from aiocache import caches, Cache, BaseCache
from aiocache.serializers import PickleSerializer
from fastapi import Depends, Request
from sqlmodel import select
from typing_extensions import Annotated

import cea.config
from cea.interfaces.dashboard.lib.logs import logger, getCEAServerLogger
from cea.interfaces.dashboard.lib.auth.providers import StackAuth
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

IGNORE_CONFIG_SECTIONS = {"server", "development", "schemas"}

settings = get_settings()
cea_db_config_logger = getCEAServerLogger("cea-db-config")


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
    def __init__(self, config_file: str = settings.config_path):
        if config_file.startswith("~"):
            config_file = os.path.expanduser(config_file)
        super().__init__(config_file)

    def save(self, config_file: str = settings.config_path) -> None:
        if config_file.startswith("~"):
            config_file = os.path.expanduser(config_file)
        logger.info(f"Saving config to {config_file}")
        super().save(config_file)

class CEADatabaseConfig(cea.config.Configuration):
    def __init__(self, user_id: str):
        self._user_id = user_id

        super().__init__(cea.config.DEFAULT_CONFIG)
        self.read()

    def from_dict(self, config_dict: dict):
        """
        Create a Configuration object from a dictionary.
        """
        for section_name, section_dict in config_dict.items():
            section = self.sections[section_name]
            for parameter_name, parameter_value in section_dict.items():
                parameter = section.parameters[parameter_name]
                try:
                    parameter.set(parameter_value)
                except Exception as e:
                    cea_db_config_logger.error(f"Error setting `{section_name}:{parameter_name}`: {e}")
        return self

    def to_dict(self) -> dict:
        """
        Returns the configuration as a dictionary.
        """
        out = defaultdict(dict)

        for section in self.sections.values():
            for parameter in section.parameters.values():
                try:
                    out[section.name][parameter.name] = parameter.get()
                except Exception as e:
                    cea_db_config_logger.error(f"Error reading `{section.name}:{parameter.name}`: {e}")
                    # default_value = self.default_config.get(section.name, parameter.name)
                    # print(f"Using default value: '{default_value}'")
                    # out[section.name][parameter.name] = default_value

        return out

    def read(self):
        with get_session_context() as session:
            _config = session.exec(select(Config).where(Config.user_id == self._user_id)).first()

            try:
                if _config:
                    cea_db_config_logger.info("Reading config from database")
                    self.from_dict(_config.config)
            except Exception as e:
                logger.error(e)
                cea_db_config_logger.info("Returning local config")

            return self

    def save(self, config_file: str = None) -> None:
        """Saves config to database in dict format"""
        logger.info(f"Saving config to database")
        with get_session_context() as session:
            _config = session.exec(select(Config).where(Config.user_id == self._user_id)).first()
            if _config:
                _config.config = self.to_dict()
            else:
                session.add(Config(user_id=self._user_id, config=self.to_dict()))
            session.commit()


async def get_cea_config(user: CEAUser):
    """Get configuration remote database or local file"""

    # Don't read config from database if user is local
    if settings.db_url is not None and user['id'] != LOCAL_USER_ID:
        return CEADatabaseConfig(user['id'])

    # Read config from file if config_path is set
    if settings.config_path is not None:
        return CEALocalConfig()

    raise ValueError("No config provided")


@dataclass
class ProjectInfo:
    project: str
    scenario: str


async def get_project_info(config: CEAConfig) -> ProjectInfo:
    """Get the current project and scenario in the config"""
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
        project = Project(uri=project_uri, owner=owner['id'])
        session.add(project)
        session.commit()
        session.refresh(project)

    return project.id


async def get_plot_cache(config: CEAConfig):
    _plot_cache = PlotCache(config.project)

    return _plot_cache


async def get_worker_processes():
    _cache = caches.get(CACHE_NAME)
    worker_processes = await _cache.get("worker_processes")

    if worker_processes is None:
        worker_processes = dict()
        await _cache.set("worker_processes", worker_processes)

    return AsyncDictCache(_cache, "worker_processes")


def get_server_url():
    host = settings.host
    port = settings.port
    worker_url = f"http://{host}:{port}/server"
    return worker_url


def get_project_root():
    return settings.project_root


def get_current_user(request: Request) -> dict:
    # Return local user if local mode or no remote database
    if settings.local or settings.db_url is None:
        logger.info("Using local user")
        return {'id': LOCAL_USER_ID}

    # Try to get user id from request cookie
    if StackAuth.check_token(request) is not None:
        try:
            auth_client = StackAuth.from_settings()
            auth_client.add_token_from_cookie(request)
            client = auth_client.get_current_user()

            return client
        except Exception as e:
            logger.error(e)
            # Either the token is invalid or the user is not logged in
            return {'id': LOCAL_USER_ID}

    logger.warning("Unable to determine current user, returning local user")
    return {'id': LOCAL_USER_ID}


def get_auth_client(request: Request):
    if settings.local:
        raise ValueError("Server running in local mode")

    auth_client = StackAuth.from_settings()
    auth_client.add_token_from_cookie(request)
    return auth_client


CEAUser = Annotated[dict, Depends(get_current_user)]
CEAConfig = Annotated[cea.config.Configuration, Depends(get_cea_config)]
CEAProjectInfo = Annotated[ProjectInfo, Depends(get_project_info)]
CEAProjectID = Annotated[str, Depends(get_project_id)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]
CEAWorkerProcesses = Annotated[dict, Depends(get_worker_processes)]
CEAServerUrl = Annotated[str, Depends(get_server_url)]
CEAProjectRoot = Annotated[str, Depends(get_project_root)]
CEAServerSettings = Annotated[dict, Depends(get_settings)]
CEAAuthClient = Annotated[StackAuth, Depends(get_auth_client)]
