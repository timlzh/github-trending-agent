import os
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
# Make sure you have a .env file in the root of your project
# or specify the path to your .env file like: load_dotenv(dotenv_path=".myenv")
load_dotenv()


class AISettings:
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE: str | None = os.getenv("OPENAI_API_BASE")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    SUMMARY_LANGUAGE: str = os.getenv("SUMMARY_LANGUAGE", "简体中文")


class DatabaseSettings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///github_trending.db"


class AppSettings(BaseSettings):
    """
    Application settings.
    Values are loaded from environment variables.
    """

    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "info"
    UPDATE_INTERVAL: int = 6
    OPENAI_API_KEY: Optional[str] = None


class Settings:
    """
    Application settings.
    Values are loaded from environment variables.
    """

    ai: AISettings = AISettings()
    db: DatabaseSettings = DatabaseSettings()
    app: AppSettings = AppSettings()


settings = Settings()
