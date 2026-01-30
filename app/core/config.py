from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "credit-risk-backend"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
