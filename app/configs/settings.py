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
    selenium_timeout: int = Field(default=30, validation_alias="SELENIUM_TIMEOUT")
    chromedriver_path: Path | None = Field(default=None, validation_alias="CHROMEDRIVER_PATH")
    sap_manage_sales_enquiries_url: str | None = Field(
        default=None,
        validation_alias="SAP_MANAGE_SALES_ENQUIRIES_URL",
    )
    sap_launchpad_url: str | None = Field(default=None, validation_alias="SAP_LAUNCHPAD_URL")
    sap_date_option: str = Field(default="From / To", validation_alias="SAP_DATE_OPTION")
    sap_max_invitations: int = Field(default=1, validation_alias="SAP_MAX_INVITATIONS")
    sap_skip_first_inquiry: bool = Field(default=False, validation_alias="SAP_SKIP_FIRST_INQUIRY")
    sap_settle_ms: int = Field(default=300, validation_alias="SAP_SETTLE_MS")
    scrape_date_from: str | None = Field(default=None, validation_alias="SCRAPE_DATE_FROM")
    scrape_date_to: str | None = Field(default=None, validation_alias="SCRAPE_DATE_TO")

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_dir: Path = Field(default=PROJECT_ROOT / "logs", validation_alias="LOG_DIR")
    api_host: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
