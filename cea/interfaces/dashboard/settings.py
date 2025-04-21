from functools import lru_cache
from typing import Optional

from pydantic import model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-server-settings")

ENV_VAR_PREFIX = "CEA_"


class StackAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_VAR_PREFIX + "auth_")

    project_id: Optional[str] = None
    publishable_client_key: Optional[str] = None


class Settings(BaseSettings):
    # Use "cea_" as prefix for env vars
    model_config = SettingsConfigDict(env_prefix=ENV_VAR_PREFIX)

    # Settings from cea.config
    host: Optional[str] = None
    port: Optional[int] = None
    project_root: Optional[str] = None

    db_path: Optional[str] = None
    db_url: Optional[str] = None
    user_table_name: str = "user"
    user_table_schema: str = "public"

    local: bool = Field(default=True, description="Run in local mode. Writes to local file")
    cors_origin: str = "*"

    workers: Optional[int] = Field(default=None, description="Number of workers")
    # Local only settings
    config_path: Optional[str] = "~/cea.config"

    @model_validator(mode='after')
    def validate_non_local_mode(self):
        if not self.local:
            if self.cors_origin == "*":
                logger.warning("Security warning: Running with cors_origin='*'. "
                               "This allows any origin to access your API and may pose security risks.")
            if self.db_url is None:
                raise ValueError(f"Database URL not set. Please set {(ENV_VAR_PREFIX + 'db_url').upper()}.")

            if self.project_root is None:
                raise ValueError(f"Project root not set. Please set {(ENV_VAR_PREFIX + 'project_root').upper()}.")
        return self

    def allow_path_transversal(self) -> bool:
        """
        Allow path transversal if project_root is set to empty string
        """
        return self.project_root == ""

    def to_env_file(self, path: str):
        """
        Write settings to env file in the format CEA_{KEY}={VALUE}
        """
        with open(path, "w") as f:
            for key, value in self.__dict__.items():
                if value is not None:
                    f.write(f"CEA_{key.upper()}={value}\n")
            f.flush()


@lru_cache
def get_settings():
    return Settings()
