from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/drift.db"
    log_level: str = "INFO"
    numeric_threshold: float = 0.20
    categorical_threshold: float = 0.10
    bins: int = 10
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
