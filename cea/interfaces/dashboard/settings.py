from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Use "cea_" as prefix for env vars
    model_config = SettingsConfigDict(env_prefix='cea_')

    host: Optional[str] = None
    port: Optional[int] = None
    cors_origin: str = "*"
    worker_url: Optional[str] = None
    project_root: Optional[str] = None

    def allow_path_transversal(self) -> bool:
        return self.project_root == ""


# FIXME: Settings does not load from cea config
@lru_cache
def get_settings():
    return Settings()
