from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Use "cea_" as prefix for env vars
    model_config = SettingsConfigDict(env_prefix='cea_')

    host: Optional[str] = None
    port: Optional[int] = None
    cors_origin: str = "*"
    project_root: Optional[str] = None
    database_path: Optional[str] = None

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
