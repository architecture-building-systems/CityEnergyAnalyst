from functools import lru_cache
from typing import Optional
import warnings

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Use "cea_" as prefix for env vars
    model_config = SettingsConfigDict(env_prefix='cea_')

    # Settings from cea.config
    host: Optional[str] = None
    port: Optional[int] = None
    project_root: Optional[str] = None

    db_path: Optional[str] = None
    db_url: Optional[str] = None

    local: bool = True
    cors_origin: str = "*"

    # Local only settings
    config_path: Optional[str] = "~/cea.config"

    @model_validator(mode='after')
    def validate_non_local_mode(self):
        if not self.local:
            if self.cors_origin == "*":
                warnings.warn("Security warning: Running with cors_origin='*'. "
                              "This allows any origin to access your API and may pose security risks.")
            if self.db_url is None:
                raise ValueError("Database URL not set. Please set db_url in config file.")
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
