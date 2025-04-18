from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from cea.interfaces.dashboard.settings import ENV_VAR_PREFIX

CACHE_NAME = 'cea-cache'
CONFIG_CACHE_TTL = 300


class CacheSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_VAR_PREFIX + "cache_")

    host: Optional[str] = "localhost"
    port: Optional[int] = 6379
