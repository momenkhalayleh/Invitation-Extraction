from dataclasses import dataclass

from app.configs.settings import Settings, get_settings


@dataclass(frozen=True)
class SapCredentials:
    url: str
    username: str
    password: str


def get_sap_credentials(settings: Settings | None = None) -> SapCredentials:
    config = settings or get_settings()
    return SapCredentials(
        url=config.sap_url,
        username=config.sap_username,
        password=config.sap_password,
    )
