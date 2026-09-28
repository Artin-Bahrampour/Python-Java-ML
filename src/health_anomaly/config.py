from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "service-health-anomaly-detector"
    contamination: float = 0.05
    random_state: int = 42

    model_config = SettingsConfigDict(env_prefix="ANOMALY_", extra="ignore")


settings = Settings()
