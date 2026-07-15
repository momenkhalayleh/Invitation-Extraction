from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

from app.clients.database_client import upgrade_database
from app.configs.auth import get_auth_settings
from app.configs.settings import Settings, get_settings


class SwaggerConfigurator:
    """Builds the FastAPI app with OpenAPI/Swagger metadata and shared handlers."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        version: str = "0.2.0",
        description: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self.version = version
        self.description = description or (
            "SAP invitation extraction. "
            "GET /api/invitations/today | /yesterday | /all"
        )

    def create_app(self) -> FastAPI:
        auth = get_auth_settings()
        app = FastAPI(
            title=self._settings.app_name,
            version=self.version,
            description=self.description,
            docs_url=None,
            redoc_url=None,
            openapi_url=None,
            swagger_ui_parameters={"persistAuthorization": True},
            openapi_tags=[
                {"name": "health", "description": "Service liveness."},
                {
                    "name": "invitations",
                    "description": "SAP Sales Inquiry extraction by date mode.",
                },
            ],
            lifespan=self._lifespan,
        )
        self._register_exception_handlers(app)
        self._register_docs_routes(app, auth)
        return app

    @asynccontextmanager
    async def _lifespan(self, _app: FastAPI) -> AsyncIterator[None]:
        """Run Alembic migrations once when the API process starts."""
        upgrade_database()
        yield

    @staticmethod
    def _register_docs_routes(app: FastAPI, auth) -> None:
        @app.get("/openapi.json", include_in_schema=False)
        def openapi_schema(_: None = Depends(auth.require_docs_basic)) -> JSONResponse:
            return JSONResponse(app.openapi())

        @app.get("/docs", include_in_schema=False)
        def swagger_ui(_: None = Depends(auth.require_docs_basic)) -> HTMLResponse:
            return get_swagger_ui_html(
                openapi_url="/openapi.json",
                title=f"{app.title} - Swagger UI",
            )

        @app.get("/redoc", include_in_schema=False)
        def redoc_ui(_: None = Depends(auth.require_docs_basic)) -> HTMLResponse:
            return get_redoc_html(
                openapi_url="/openapi.json",
                title=f"{app.title} - ReDoc",
            )

    @staticmethod
    def _register_exception_handlers(app: FastAPI) -> None:
        @app.exception_handler(HTTPException)
        async def http_exception_handler(
            _request: Request, exc: HTTPException
        ) -> JSONResponse:
            message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": message},
                headers=exc.headers,
            )

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            _request: Request, _exc: RequestValidationError
        ) -> JSONResponse:
            return JSONResponse(
                status_code=400, content={"error": "Invalid request parameters"}
            )

        @app.exception_handler(Exception)
        async def unhandled_exception_handler(
            _request: Request, _exc: Exception
        ) -> JSONResponse:
            return JSONResponse(
                status_code=500, content={"error": "Internal server error"}
            )
