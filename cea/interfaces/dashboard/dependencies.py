from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass

from aiocache import caches, Cache, BaseCache
from aiocache.serializers import PickleSerializer
from fastapi import Depends, Request, HTTPException, status
from sqlmodel import select
from typing_extensions import Annotated

import cea.config
from cea.interfaces.dashboard.lib.auth import CEAAuthError
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
CONFIG_CACHE_TTL = 300
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
        if not settings.local:
            logger.warning("Using local config in non-local mode")

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

    def __getstate__(self) -> str:
        # Add user_id to state when pickling
        string = super().__getstate__()
        return f"{self._user_id}\n{string}"

    def __setstate__(self, state: str):
        # Read user_id from state when unpickling
        user_id, string = state.split("\n", 1)
        self._user_id = user_id

        super().__setstate__(string)

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
                    cea_db_config_logger.warning(f"Reading remote config: `{self._user_id}`")
                    self.from_dict(_config.config)
            except Exception as e:
                logger.error(e)
                cea_db_config_logger.warning("Returning local config")

        return self

    def save(self, config_file: str = None) -> None:
        """Saves config to database in dict format"""
        logger.info("Saving config to database")
        with get_session_context() as session:
            _config = session.exec(select(Config).where(Config.user_id == self._user_id)).first()
            if _config:
                _config.config = self.to_dict()
            else:
                session.add(Config(user_id=self._user_id, config=self.to_dict()))
            session.commit()

        # Invalidate cache
        async def invalidate_cache():
            _cache = caches.get(CACHE_NAME)
            cache_key = f"cea_config_{self._user_id}"
            await _cache.delete(cache_key)
            cea_db_config_logger.debug(f"Invalidated config cache for user: {self._user_id}")

        # Run in event loop
        import asyncio
        try:
            asyncio.create_task(invalidate_cache())
        except RuntimeError:
            # If no event loop is running
            loop = asyncio.new_event_loop()
            loop.run_until_complete(invalidate_cache())
            loop.close()


async def get_cea_config(user_id: CEAUserID):
    """Get configuration remote database or local file"""

    # Don't read config from database if user is local
    if settings.db_url is not None and user_id != LOCAL_USER_ID:
        # Try to get config from cache first
        _cache = caches.get(CACHE_NAME)
        cache_key = f"cea_config_{user_id}"

        # Try to get from cache
        config = await _cache.get(cache_key)
        if config is not None:
            cea_db_config_logger.debug(f"Using cached config for user: {user_id}")
            return config

        # Cache miss, read from database
        cea_db_config_logger.debug(f"Cache miss, reading config from database for user: {user_id}")
        config = CEADatabaseConfig(user_id)

        # Cache the config
        await _cache.set(cache_key, config, ttl=CONFIG_CACHE_TTL)
        return config

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


def create_project(project_uri: str, owner_id: CEAUserID, session: SessionDep) -> Project:
    project = Project(uri=project_uri, owner=owner_id)
    session.add(project)
    session.commit()
    session.refresh(project)

    return project


async def get_project_id(session: SessionDep, owner_id: CEAUserID,
                         project_root: CEAProjectRoot, project_info: CEAProjectInfo):
    """Get the project ID from the project URI."""
    project_uri = project_info.project
    if project_root is not None:
        project_uri = os.path.join(project_root, project_uri)

    project = session.exec(select(Project).where(Project.uri == project_uri)).first()

    # If project not found, create a new one
    if not project:
        logger.info(f"Creating project in database: {project_uri}")
        project = create_project(project_uri, owner_id, session)

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


def get_project_root(user_id: CEAUserID):
    """Get the project root for the current user"""
    project_root = settings.project_root

    if not settings.local:
        project_root = os.path.join(project_root, user_id)

    logger.info(f"Using project root: {project_root}")
    return project_root


def get_user_id(request: Request) -> dict:
    # Return local user if local mode
    if settings.local:
        logger.info(f"Using `{LOCAL_USER_ID}`")
        return LOCAL_USER_ID

    # Try to get user id from request cookie
    if (token := StackAuth.get_token(request)) is not None:
        try:
            auth_client = StackAuth(token)
            return auth_client.get_user_id()
        except CEAAuthError as e:
            logger.error(e)
            # raise Exception("Unable to verify user token")

    logger.info(f"Unable to determine current user, using `{LOCAL_USER_ID}`")
    return LOCAL_USER_ID


def get_user(request: Request):
    if settings.local:
        return {'id': LOCAL_USER_ID}

    # Try to get user id from request cookie
    if (token := StackAuth.get_token(request)) is not None:
        try:
            auth_client = StackAuth(token)
            return auth_client.get_current_user()
        except CEAAuthError as e:
            logger.error(e)
            # raise Exception("Unable to verify user token")

    logger.info(f"Unable to determine current user, using `{LOCAL_USER_ID}`")
    return {'id': LOCAL_USER_ID}


def get_auth_client(request: Request):
    if settings.local:
        raise ValueError("Server running in local mode")

    if (token := StackAuth.get_token(request)) is not None:
        return StackAuth(token)

    raise Exception("Unable get auth client")


def check_auth_for_demo(request: Request, user_id: CEAUserID):
    """Check if user is authorized when not in local mode"""

    # Pass if local mode
    if settings.local:
        return

    # Check if user is authorized
    if user_id == LOCAL_USER_ID:
        logger.info(f"Unauthorized access \"{request.method} {request.url.path}\": `{user_id}`")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


CEAUserID = Annotated[str, Depends(get_user_id)]
CEAUser = Annotated[dict, Depends(get_user)]
CEAConfig = Annotated[cea.config.Configuration, Depends(get_cea_config)]
CEAProjectInfo = Annotated[ProjectInfo, Depends(get_project_info)]
CEAProjectID = Annotated[str, Depends(get_project_id)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]
CEAWorkerProcesses = Annotated[dict, Depends(get_worker_processes)]
CEAServerUrl = Annotated[str, Depends(get_server_url)]
CEAProjectRoot = Annotated[str, Depends(get_project_root)]
CEAServerSettings = Annotated[dict, Depends(get_settings)]
CEAAuthClient = Annotated[StackAuth, Depends(get_auth_client)]

CEASeverDemoAuthCheck = Depends(check_auth_for_demo)
