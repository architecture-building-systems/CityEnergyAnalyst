from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from cea.interfaces.dashboard.constants import ENV_VAR_PREFIX

CACHE_NAME = 'cea-cache'
CONFIG_CACHE_TTL = 300  # 5 minutes for config cache

# TTL settings for different cache types
STREAM_CACHE_TTL = 3600  # 1 hour - streams cleaned up after job completion
WORKER_PROCESS_TTL = 7200  # 2 hours - fallback cleanup for orphaned worker process tracking
DEFAULT_CACHE_TTL = 1800  # 30 minutes - default for other cache entries


class CacheSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_VAR_PREFIX + "cache_",
                                      env_file=('.env', '.env.local'), extra="ignore")

    host: Optional[str] = None
    port: int = 6379


cache_settings = CacheSettings()
