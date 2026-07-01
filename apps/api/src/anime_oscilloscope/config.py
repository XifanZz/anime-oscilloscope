from datetime import date
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )

    env: str = "development"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/anime_oscilloscope"
    repository_backend: Literal["demo", "postgres"] = "demo"
    tracking_launch_date: date = date(2026, 7, 1)
    bangumi_token: str | None = None
    mal_client_id: str | None = None
    project_url: str = "https://github.com/XifanZz/anime-oscilloscope"
    semantic_backend: Literal["hash", "bge"] = "hash"
    semantic_model_name: str = "BAAI/bge-small-zh-v1.5"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
