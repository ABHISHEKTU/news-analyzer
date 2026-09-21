# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./news.db"
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()