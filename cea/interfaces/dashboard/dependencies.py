from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Dict, Union

from fastapi import Depends, Request, HTTPException, status
from sqlmodel import select
from typing_extensions import Annotated

import cea.config
from cea.interfaces.dashboard.lib.auth import CEAAuthError
from cea.interfaces.dashboard.lib.auth.providers import StackAuth, AuthClient
from cea.interfaces.dashboard.lib.cache.base import AsyncDictCache
from cea.interfaces.dashboard.lib.cache.provider import get_cache, get_dict_cache
from cea.interfaces.dashboard.lib.cache.settings import CONFIG_CACHE_TTL
from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID, Project, Config
from cea.interfaces.dashboard.lib.database.session import SessionDep, get_session_context
from cea.interfaces.dashboard.lib.database.settings import database_settings
from cea.interfaces.dashboard.lib.logs import logger, getCEAServerLogger
from cea.interfaces.dashboard.settings import get_settings
from cea.plots.cache import PlotCache

IGNORE_CONFIG_SECTIONS = {"server", "development", "schemas"}

settings = get_settings()
cea_db_config_logger = getCEAServerLogger("cea-db-config")


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

    async def read(self) -> None:
        logger.info("Reading config from database")

        # Try to get config from cache first
        _cache = get_cache()
        cache_key = f"cea_config_{self._user_id}"

        # Try to get from cache
        config = await _cache.get(cache_key)
        if config is not None:
            cea_db_config_logger.debug(f"Using cached config for user: {self._user_id}")
            self.user_config = config.user_config
            return
        else:
            logger.warning(f"Cache miss: {self._user_id}")

        async with get_session_context() as session:
            try:
                result = await session.execute(select(Config).where(Config.user_id == self._user_id))
                _config = result.scalar()
                if _config:
                    cea_db_config_logger.warning(f"Reading remote config: `{self._user_id}`")
                    self.from_dict(_config.config)
            except Exception as e:
                logger.error(e)
                cea_db_config_logger.warning("Returning local config")

    async def save(self, config_file: str = None) -> None:
        """Saves config to database in dict format"""
        logger.info("Saving config to database")

        # Update config object in cache
        _cache = get_cache()
        cache_key = f"cea_config_{self._user_id}"

        await _cache.set(cache_key, self, ttl=CONFIG_CACHE_TTL)
        cea_db_config_logger.debug(f"Updated config cache for user: {self._user_id}")

        # Save new config to database
        async def _save_to_db():
            config_dict = self.to_dict()
            async with get_session_context() as session:
                result = await session.execute(select(Config).where(Config.user_id == self._user_id))
                _config = result.scalar()
                if _config:
                    _config.config = config_dict
                else:
                    session.add(Config(user_id=self._user_id, config=config_dict))

        asyncio.create_task(_save_to_db())

async def get_cea_config(user_id: CEAUserID) -> cea.config.Configuration:
    """Get configuration remote database or local file"""

    # Don't read config from database if user is local
    if database_settings.url is not None and user_id != LOCAL_USER_ID:
        config = CEADatabaseConfig(user_id)
        await config.read()
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
        project=str(config.project),
        scenario=str(config.scenario),
    )


async def create_project(project_uri: str, owner_id: CEAUserID, session: SessionDep) -> Project:
    project = Project(uri=project_uri, owner=owner_id)
    session.add(project)
    await session.commit()
    await session.refresh(project)

    return project


async def get_project_id(session: SessionDep, owner_id: CEAUserID,
                         project_root: CEAProjectRoot, project_info: CEAProjectInfo):
    """Get the project ID from the project URI."""
    project_uri = project_info.project
    if project_root is not None:
        project_uri = os.path.join(project_root, project_uri)

    result = await session.execute(select(Project).where(Project.uri == project_uri))
    project = result.scalar()

    # If project not found, create a new one
    if not project:
        logger.info(f"Creating project in database: {project_uri}")
        project = await create_project(project_uri, owner_id, session)

    return project.id


async def get_plot_cache(config: CEAConfig):
    _plot_cache = PlotCache(config.project)

    return _plot_cache


async def get_worker_processes() -> AsyncDictCache:
    return await get_dict_cache("worker_processes")


async def get_streams() -> AsyncDictCache:
    return await get_dict_cache("streams")


def get_server_url():
    host = settings.host
    port = settings.port
    worker_url = f"http://{host}:{port}/server"
    return worker_url


def get_project_root(user_id: CEAUserID) -> Optional[str]:
    """Get the project root for the current user"""
    project_root = settings.project_root

    # Use user ID as project root for non-local mode
    if not settings.local:
        if project_root is None:
            raise ValueError("Project root not set. Unable to determine project root.")
        project_root = os.path.join(os.path.normpath(project_root), user_id)

    logger.info(f"Using project root: {project_root}")
    return project_root


def get_user_id(auth_client: CEAAuthClient) -> str:
    # Return local user if local mode
    if settings.local:
        logger.info(f"Using `{LOCAL_USER_ID}`")
        return LOCAL_USER_ID

    # Try to get user id from request cookie
    if auth_client is not None:
        try:
            return auth_client.get_user_id()
        except CEAAuthError as e:
            logger.error(e)
            # raise Exception("Unable to verify user token")

    logger.info(f"Unable to determine current user, using `{LOCAL_USER_ID}`")
    return LOCAL_USER_ID


def get_user(auth_client: CEAAuthClient) -> Dict[str, str]:
    if settings.local:
        return {'id': LOCAL_USER_ID}

    # Try to get user id from request cookie
    if auth_client is not None:
        try:
            return auth_client.get_current_user()
        except CEAAuthError as e:
            logger.error(e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    logger.info(f"Unable to determine current user, using `{LOCAL_USER_ID}`")
    return {'id': LOCAL_USER_ID}


def get_auth_client(request: Request) -> Optional[AuthClient]:
    if settings.local:
        return None

    auth_client = StackAuth.from_request_cookies(request.cookies)
    if auth_client.access_token is not None:
        return auth_client

    logger.debug("Unable to determine auth client")
    return None


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
CEAConfig = Annotated[Union[CEALocalConfig, CEADatabaseConfig], Depends(get_cea_config)]
CEAProjectInfo = Annotated[ProjectInfo, Depends(get_project_info)]
CEAProjectID = Annotated[str, Depends(get_project_id)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]
CEAWorkerProcesses = Annotated[AsyncDictCache, Depends(get_worker_processes)]
CEAStreams = Annotated[AsyncDictCache, Depends(get_streams)]
CEAServerUrl = Annotated[str, Depends(get_server_url)]
CEAProjectRoot = Annotated[Optional[str], Depends(get_project_root)]
CEAServerSettings = Annotated[dict, Depends(get_settings)]
CEAAuthClient = Annotated[AuthClient, Depends(get_auth_client)]

CEASeverDemoAuthCheck = Depends(check_auth_for_demo)
