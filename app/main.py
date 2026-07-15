from fastapi import FastAPI

from app.api.routes.invitations import router as invitations_router
from app.configs.settings import get_settings
from app.configs.swagger import SwaggerConfigurator

settings = get_settings()

app: FastAPI = SwaggerConfigurator(settings).create_app()


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(invitations_router, prefix="/api")
