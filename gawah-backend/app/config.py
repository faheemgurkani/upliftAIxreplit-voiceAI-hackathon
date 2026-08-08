from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Gawah API"
    app_env: str = "development"
    debug: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    vapi_api_key: str = ""
    vapi_webhook_secret: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    uplift_orator_key: str = ""
    uplift_orator_base_url: str = "https://api.upliftai.org/v1"

    supabase_url: str = ""
    supabase_key: str = ""

    case_id_secret: str = "change-me-in-production"
    local_db_path: str = "data/gawah_store.json"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @property
    def cors_origin_list(self) -> List[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins or ["*"]

    @property
    def use_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
