"""Tests for invitation extraction API endpoints."""

from collections.abc import Generator
from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.configs.settings import get_settings
from app.controllers.invitation_controllers import (
    InvitationExtractionError,
    InvitationNotFoundError,
)
from app.main import app
from app.schemas.invitation import InvitationCreate


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with patch("app.configs.swagger.upgrade_database"):
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client


def _sample_invitation(inv_ref: str = "UAE1401324") -> InvitationCreate:
    return InvitationCreate(
        inv_ref=inv_ref,
        customer_ref="2182600106",
        customer_name="Test Customer",
        inv_subject="Test Subject",
        closing_date=date(2026, 1, 15),
    )


@pytest.mark.parametrize("mode", ["today", "yesterday", "all"])
def test_mode_endpoints_empty(client: TestClient, mode: str) -> None:
    with patch(
        "app.controllers.invitation_controllers.invitation_controller.extract_invitations_via_api",
        return_value=[],
    ) as mocked:
        response = client.get(f"/api/invitations/{mode}")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == mode
    assert body["data"] == []
    assert body["count"] == 0
    assert mocked.call_args.kwargs["mode"] == mode
    assert mocked.call_args.kwargs["headless"] is False


@pytest.mark.parametrize("mode", ["today", "yesterday", "all"])
def test_mode_endpoints_with_data(client: TestClient, mode: str) -> None:
    with patch(
        "app.controllers.invitation_controllers.invitation_controller.extract_invitations_via_api",
        return_value=[_sample_invitation()],
    ) as mocked:
        response = client.get(f"/api/invitations/{mode}")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == mode
    assert body["count"] == 1
    assert body["data"][0]["invitationId"] == "UAE1401324"
    assert mocked.call_args.kwargs["mode"] == mode


def test_today_by_valid_id(client: TestClient) -> None:
    with patch(
        "app.controllers.invitation_controllers.invitation_controller.extract_invitations_via_api",
        return_value=_sample_invitation(),
    ) as mocked:
        response = client.get(
            "/api/invitations/today",
            params={"invitationId": "UAE1401324"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["invitationId"] == "UAE1401324"
    assert body["data"]["customer_ref"] == "2182600106"
    assert mocked.call_args.kwargs["mode"] == "today"
    assert mocked.call_args.kwargs["invitation_id"] == "UAE1401324"


def test_invalid_invitation_id(client: TestClient) -> None:
    response = client.get(
        "/api/invitations/yesterday",
        params={"invitationId": "not-valid"},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid invitationId format"


def test_invitation_not_found(client: TestClient) -> None:
    with patch(
        "app.controllers.invitation_controllers.invitation_controller.extract_invitations_via_api",
        side_effect=InvitationNotFoundError(
            "Invitation UAE9999999 not found in search results"
        ),
    ):
        response = client.get(
            "/api/invitations/all",
            params={"invitationId": "UAE9999999"},
        )

    assert response.status_code == 404
    assert "not found" in response.json()["error"]


def test_sap_error(client: TestClient) -> None:
    with patch(
        "app.controllers.invitation_controllers.invitation_controller.extract_invitations_via_api",
        side_effect=InvitationExtractionError(
            "Could not select Document Date option 'Yesterday'"
        ),
    ):
        response = client.get("/api/invitations/yesterday")

    assert response.status_code == 400
    assert "Yesterday" in response.json()["error"]


def test_docs_requires_authentication(client: TestClient) -> None:
    assert client.get("/docs").status_code == 401
    assert client.get("/redoc").status_code == 401
    assert client.get("/openapi.json").status_code == 401


def test_docs_with_valid_credentials(client: TestClient) -> None:
    settings = get_settings()
    auth = (settings.docs_username, settings.docs_password)

    assert client.get("/docs", auth=auth).status_code == 200
    assert client.get("/redoc", auth=auth).status_code == 200
    assert client.get("/openapi.json", auth=auth).status_code == 200


def test_docs_rejects_invalid_credentials(client: TestClient) -> None:
    assert client.get("/docs", auth=("wrong", "credentials")).status_code == 401
