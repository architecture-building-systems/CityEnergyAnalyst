from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from cea.interfaces.dashboard.constants import ENV_VAR_PREFIX

CACHE_NAME = 'cea-cache'
CONFIG_CACHE_TTL = 300


class CacheSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_VAR_PREFIX + "cache_",
                                      env_file=('.env', '.env.local'), extra="ignore")

    host: Optional[str] = None
    port: int = 6379


cache_settings = CacheSettings()
