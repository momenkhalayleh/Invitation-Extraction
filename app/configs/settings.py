from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sap_url: str = Field(validation_alias="SAP_URL")
    sap_username: str = Field(validation_alias="SAP_USERNAME")
    sap_password: str = Field(validation_alias="SAP_PASSWORD")

    database_url: str = Field(validation_alias="DATABASE_URL")

    headless: bool = Field(default=True, validation_alias="HEADLESS")
    scrape_date_from: str | None = Field(default=None, validation_alias="SCRAPE_DATE_FROM")
    scrape_date_to: str | None = Field(default=None, validation_alias="SCRAPE_DATE_TO")

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_dir: Path = Field(default=PROJECT_ROOT / "logs", validation_alias="LOG_DIR")


@lru_cache
def get_settings() -> Settings:
    return Settings()
