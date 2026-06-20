from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Kanpai POS", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    database_url: str = Field(
        default="sqlite:///./data/kanpai_pos.db",
        alias="DATABASE_URL",
    )
    kanpai_admin_pin: str = Field(default="1234", alias="KANPAI_ADMIN_PIN")
    auth_session_hours: int = Field(default=12, alias="KANPAI_SESSION_HOURS")
    labsmobile_user: str | None = Field(default=None, alias="LABSMOBILE_USER")
    labsmobile_token: str | None = Field(default=None, alias="LABSMOBILE_TOKEN")
    labsmobile_test_mode: bool = Field(default=True, alias="LABSMOBILE_TEST_MODE")
    labsmobile_default_msisdn: str | None = Field(
        default=None, alias="LABSMOBILE_DEFAULT_MSISDN"
    )
    sms_enabled: bool = Field(default=False, alias="SMS_ENABLED")
    airtable_api_token: str | None = Field(default=None, alias="AIRTABLE_API_TOKEN")
    airtable_base_id: str | None = Field(default=None, alias="AIRTABLE_BASE_ID")
    airtable_sync_enabled: bool = Field(
        default=False, alias="AIRTABLE_SYNC_ENABLED"
    )
    airtable_sync_interval_minutes: int = Field(
        default=60, ge=30, alias="AIRTABLE_SYNC_INTERVAL_MINUTES"
    )
    airtable_sync_pull_enabled: bool = Field(
        default=True, alias="AIRTABLE_SYNC_PULL_ENABLED"
    )
    airtable_sync_push_enabled: bool = Field(
        default=True, alias="AIRTABLE_SYNC_PUSH_ENABLED"
    )
    airtable_sync_run_on_startup: bool = Field(
        default=False, alias="AIRTABLE_SYNC_RUN_ON_STARTUP"
    )
    airtable_sync_skip_pull_during_active_shift: bool = Field(
        default=True, alias="AIRTABLE_SYNC_SKIP_PULL_DURING_ACTIVE_SHIFT"
    )

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        """Acepta perfiles habituales además de booleanos explícitos."""
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
