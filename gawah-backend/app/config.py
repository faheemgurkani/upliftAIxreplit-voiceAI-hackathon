from functools import lru_cache
from typing import List

from pydantic import field_validator
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

    # Uplift AI — Singapore for Pakistan latency + phone calling
    upliftai_api_key: str = ""
    uplift_assistant_id: str = ""
    uplift_base_url: str = "https://ap-southeast-1.api.upliftai.org/v1"
    uplift_tts_voice_id: str = "ai_lwr_f_fb"
    uplift_tts_output_format: str = "MP3_22050_128"

    # Groq (LLM for structuring / consistency / corroboration)
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # OpenAI optional fallback
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # Twilio (optional PSTN bridge)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # NGO escalation
    ngo_webhook_url: str = ""

    case_id_secret: str = "change-me-in-production"
    local_db_path: str = "data/gawah_store.json"
    local_audio_dir: str = "data/audio"

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
        key = self.supabase_service_key or self.supabase_key
        return bool(self.supabase_url and key)

    @property
    def supabase_anon_or_service_key(self) -> str:
        return self.supabase_service_key or self.supabase_key

    @property
    def uplift_enabled(self) -> bool:
        return bool(self.upliftai_api_key)

    @property
    def groq_enabled(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def llm_enabled(self) -> bool:
        return self.groq_enabled or bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
