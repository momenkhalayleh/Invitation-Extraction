import secrets
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.configs.settings import Settings, get_settings

http_basic = HTTPBasic(auto_error=False)


@dataclass(frozen=True)
class SapCredentials:
    url: str
    username: str
    password: str


@dataclass(frozen=True)
class AuthSettings:
    settings: Settings

    def require_docs_basic(
        self,
        credentials: HTTPBasicCredentials | None = Depends(http_basic),
    ) -> None:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Basic"},
            )

        username_ok = secrets.compare_digest(
            credentials.username, self.settings.docs_username
        )
        password_ok = secrets.compare_digest(
            credentials.password, self.settings.docs_password
        )
        if not (username_ok and password_ok):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )


def get_sap_credentials(settings: Settings | None = None) -> SapCredentials:
    config = settings or get_settings()
    return SapCredentials(
        url=config.sap_url,
        username=config.sap_username,
        password=config.sap_password,
    )


@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings(settings=get_settings())
