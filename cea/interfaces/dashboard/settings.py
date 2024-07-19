from functools import lru_cache
from typing import Optional, List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Use "cea_" as prefix for env vars
    model_config = SettingsConfigDict(env_prefix='cea_')

    host: Optional[str] = None
    port: Optional[int] = None
    cors_origins: List[str] = ["*"]
    worker_url: Optional[str] = None


@lru_cache
def get_settings():
    return Settings()
