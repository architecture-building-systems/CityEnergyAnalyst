from functools import lru_cache
import os
from typing import Optional

from pydantic import model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from cea.interfaces.dashboard.constants import ENV_VAR_PREFIX
from cea.interfaces.dashboard.lib.cache.settings import cache_settings
from cea.interfaces.dashboard.lib.database.settings import database_settings
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-server-settings")


class StackAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_VAR_PREFIX + "auth_",
                                      env_file=('.env', '.env.local'), extra="ignore")

    project_id: Optional[str] = None
    publishable_client_key: Optional[str] = None


class LimitSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_VAR_PREFIX + "limit_",
                                      env_file=('.env', '.env.local'), extra="ignore")
    num_projects: Optional[int] = None
    num_scenarios: Optional[int] = None
    num_buildings: Optional[int] = None


class Settings(BaseSettings):
    # Use "cea_" as prefix for env vars
    model_config = SettingsConfigDict(env_prefix=ENV_VAR_PREFIX,
                                      env_file=('.env', '.env.local'), extra="ignore")

    # Settings from cea.config
    host: Optional[str] = None
    port: Optional[int] = None
    project_root: Optional[str] = None

    local: bool = Field(default=True, description="Run in local mode. Writes to local file")
    cors_origin: str = "http://localhost:5050"

    workers: Optional[int] = Field(default=None, description="Number of workers")

    # Local only settings
    config_path: Optional[str] = "~/cea.config"

    @model_validator(mode='after')
    def validate_cors_origin(self):
        """
        Validate CORS origin format and security.

        This validator handles all CORS-related validation including:
        - Blocking wildcard origins in production mode
        - Validating URL format for specific origins
        - Supporting comma-separated multiple origins
        """
        if self.cors_origin == "*":
            if not self.local:
                raise ValueError(
                    f"Wildcard CORS origin ('*') is not allowed in non-local mode. "
                    f"Please set {(ENV_VAR_PREFIX + 'cors_origin').upper()} to your frontend URL(s)."
                )
            # Allow wildcard in local mode, but warn
            logger.warning(
                "Using wildcard CORS origin ('*'). This is only safe for local development. "
                "For production, set CEA_CORS_ORIGIN to specific domain(s)."
            )
            return self

        # Validate each origin in comma-separated list
        import re
        origins = [o.strip() for o in self.cors_origin.split(",")]
        pattern = r'^https?://[a-zA-Z0-9\-\.:]+(:[0-9]+)?$'

        for origin in origins:
            if not re.match(pattern, origin):
                raise ValueError(
                    f"Invalid CORS origin format: '{origin}'. "
                    "Expected format: http://hostname[:port] or https://hostname[:port]"
                )

        return self

    @model_validator(mode='after')
    def validate_non_local_mode(self):
        """
        Validate required settings for non-local mode
        """
        if not self.local:
            if database_settings.url is None:
                raise ValueError(f"Database URL not set. Please set {(ENV_VAR_PREFIX + 'db_url').upper()}.")

            if self.project_root is None:
                raise ValueError(f"Project root not set. Please set {(ENV_VAR_PREFIX + 'project_root').upper()}.")
        return self

    @model_validator(mode='after')
    def validate_multi_worker_mode(self):
        """External cache is required for multiple workers to work"""
        if self.workers:
            # TODO: Maybe check connection
            if cache_settings.host is None or cache_settings.port is None:
                raise ValueError("External cache settings required for multiple workers")

        return self

    def allow_path_transversal(self) -> bool:
        """
        Allow path transversal if project_root is not set
        """
        return self.project_root is None

    def to_env_vars(self):
        """
        Write settings to env variables in the format {ENV_VAR_PREFIX}{KEY}={VALUE}
        """
        # Set environment variables 
        for key, value in self.__dict__.items():
            if value is not None:
                env_var_name = f"{ENV_VAR_PREFIX}{key.upper()}"
                os.environ[env_var_name] = str(value)


@lru_cache
def get_settings():
    return Settings()
