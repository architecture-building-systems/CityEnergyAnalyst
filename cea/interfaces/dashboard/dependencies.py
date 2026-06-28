from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Dict

from fastapi import Depends, Request, HTTPException, status
from sqlmodel import select
from typing_extensions import Annotated

import cea.config
from cea.interfaces.dashboard.lib.auth import CEAAuthError
from cea.interfaces.dashboard.lib.auth.providers import StackAuth, AuthClient
from cea.interfaces.dashboard.lib.cache.base import AsyncDictCache
from cea.interfaces.dashboard.lib.cache.provider import get_dict_cache
from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID, Project
from cea.interfaces.dashboard.lib.database.session import SessionDep
from cea.interfaces.dashboard.lib.logs import logger
from cea.interfaces.dashboard.settings import Settings, get_settings, LimitSettings
from cea.plots.cache import PlotCache

IGNORE_CONFIG_SECTIONS = {"server", "development", "schemas"}


class CEALocalConfig(cea.config.Configuration):
    def __init__(self, config_file: str):
        self._config_path = config_file
        super().__init__(os.path.expanduser(config_file))

    def save(self, config_file: str = None) -> None:
        path = config_file if config_file is not None else self._config_path
        logger.info(f"Saving config to {path}")
        super().save(os.path.expanduser(path))


class CEAStatelessConfig(cea.config.Configuration):
    """Per-request config for non-local (cloud) mode.

    Built fresh from DEFAULT_CONFIG on each request. save() is a no-op so
    nothing is ever persisted server-side, enabling stateless horizontal scaling.

    The no-op save() also neutralises the init-time self.save() in
    Configuration.__init__ (fired when ~/cea.config is absent, e.g. in containers).
    """

    def __init__(self):
        super().__init__(cea.config.DEFAULT_CONFIG)

    def save(self, config_file: str = None) -> None:
        logger.debug("save() is a no-op in non-local (stateless) mode")


def get_cea_config(settings: CEAServerSettings) -> cea.config.Configuration:
    """Return a config instance for this request.

    Local mode: disk-backed CEALocalConfig (reads/writes ~/cea.config, keeps
    CLI parity). Non-local mode: fresh CEAStatelessConfig built from
    DEFAULT_CONFIG with a no-op save() for stateless horizontal scaling.
    """
    if settings.local:
        if settings.config_path is None:
            raise ValueError("No config provided")
        return CEALocalConfig(settings.config_path)
    return CEAStatelessConfig()


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
    from cea.interfaces.dashboard.lib.cache.settings import WORKER_PROCESS_TTL
    return await get_dict_cache("worker_processes", default_ttl=WORKER_PROCESS_TTL)


async def get_streams() -> AsyncDictCache:
    from cea.interfaces.dashboard.lib.cache.settings import STREAM_CACHE_TTL
    return await get_dict_cache("streams", default_ttl=STREAM_CACHE_TTL)


def get_server_url(settings: CEAServerSettings) -> str:
    host = settings.host
    port = settings.port
    worker_url = f"http://{host}:{port}/server"
    return worker_url


def get_project_root(user_id: CEAUserID, settings: CEAServerSettings) -> Optional[str]:
    """Get the project root for the current user"""
    project_root = settings.project_root

    # Use user ID as project root for non-local mode
    if not settings.local:
        if project_root is None:
            raise ValueError("Project root not set. Unable to determine project root.")
        project_root = os.path.join(os.path.normpath(project_root), user_id)

    logger.debug(f"Using project root: {project_root}")
    return project_root


def get_user_id(auth_client: CEAAuthClient, settings: CEAServerSettings) -> str:
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


def get_user(auth_client: CEAAuthClient, settings: CEAServerSettings) -> Dict[str, str]:
    if settings.local:
        return {'id': LOCAL_USER_ID}

    # Try to get user id from request cookie
    if auth_client is not None:
        try:
            user = auth_client.get_current_user()
            if user.get("client_read_only_metadata") is None:
                user["onboarded"] = False
                user["pro_user"] = False
            else:
                user["onboarded"] = user['client_read_only_metadata'].get("onboarded", False)
                user["pro_user"] = user['client_read_only_metadata'].get("pro_user", False)
            return user
        except CEAAuthError as e:
            logger.error(e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    logger.info(f"Unable to determine current user, using `{LOCAL_USER_ID}`")
    return {'id': LOCAL_USER_ID}


def get_auth_client(request: Request, settings: CEAServerSettings) -> Optional[AuthClient]:
    if settings.local:
        return None

    auth_client = StackAuth.from_request_cookies(request.cookies)
    if auth_client.access_token is not None:
        return auth_client

    logger.debug("Unable to determine auth client")
    return None


# Routes publicly accessible without authentication in non-local mode.
# Every other route is gated by require_authenticated (applied at app level).
_PUBLIC_ROUTES: frozenset = frozenset({
    "/api/user/session/refresh",  # token refresh — must work with an expired access token
    "/api/user/logout",           # session teardown — should work even if token is stale
    "/server/alive",              # health check — monitoring must not need a session
    "/server/version",            # version info — safe to expose publicly
})

# Path prefixes exempt from session auth. The route handler is responsible for
# its own auth when its path matches one of these prefixes.
_PUBLIC_ROUTE_PREFIXES: tuple = (
    "/api/downloads/",  # pre-signed token downloads — anchor tags don't send cookies
)


def require_authenticated(request: Request, user_id: CEAUserID, settings: CEAServerSettings):
    """App-level auth guard: every route requires an authenticated user in non-local mode.

    In local (single-user desktop) mode this is a no-op — all routes are open.
    In non-local mode any caller that resolves to LOCAL_USER_ID (the anonymous
    sentinel returned when no valid session token is present) receives 401.

    Routes in _PUBLIC_ROUTES / _PUBLIC_ROUTE_PREFIXES are explicitly excluded.
    No proxy is assumed — the server self-enforces auth.
    """
    if settings.local:
        return
    if request.url.path in _PUBLIC_ROUTES:
        return
    if request.url.path.startswith(_PUBLIC_ROUTE_PREFIXES):
        return
    if user_id == LOCAL_USER_ID:
        # FIXME: LOCAL_USER_ID is overloaded — it is the sentinel for both the
        # local-desktop user (harmless; local mode exits above) and anonymous
        # callers in non-local mode. Rename / split these two concepts so the
        # guard here is unambiguous.
        safe_path = request.url.path.replace("\r", "\\r").replace("\n", "\\n")
        logger.info('Unauthenticated access "%s %s"', request.method, safe_path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

def get_limits(user: CEAUser) -> LimitSettings:
    # TODO: Shift limits to user properties
    limits = LimitSettings()

    # Pro users get 5x the limits and 5 scenarios
    if user.get("pro_user", False):
        limits.num_projects = limits.num_projects * 5 if limits.num_projects else None
        limits.num_scenarios = 5
        limits.num_buildings = limits.num_buildings * 5 if limits.num_buildings else None

    return limits


CEAUserID = Annotated[str, Depends(get_user_id)]
CEAUser = Annotated[dict, Depends(get_user)]
CEAConfig = Annotated[cea.config.Configuration, Depends(get_cea_config)]
CEAProjectInfo = Annotated[ProjectInfo, Depends(get_project_info)]
CEAProjectID = Annotated[str, Depends(get_project_id)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]
CEAWorkerProcesses = Annotated[AsyncDictCache, Depends(get_worker_processes)]
CEAStreams = Annotated[AsyncDictCache, Depends(get_streams)]
CEAServerUrl = Annotated[str, Depends(get_server_url)]
CEAProjectRoot = Annotated[Optional[str], Depends(get_project_root)]
CEAServerSettings = Annotated[Settings, Depends(get_settings)]
CEAAuthClient = Annotated[AuthClient, Depends(get_auth_client)]
CEAServerLimits = Annotated[LimitSettings, Depends(get_limits)]

RequireAuthenticated = Depends(require_authenticated)
