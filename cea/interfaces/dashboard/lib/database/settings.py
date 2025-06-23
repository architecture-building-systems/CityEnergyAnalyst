from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from cea.interfaces.dashboard.constants import ENV_VAR_PREFIX


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_VAR_PREFIX + "db_",
                                      env_file=('.env', '.env.local'), extra="ignore")

    path: Optional[str] = None
    # TODO: Parse url using sqlalchemy
    url: Optional[str] = None

    user_table_name: str = "user"
    user_table_schema: str = "public"


database_settings = DatabaseSettings()
