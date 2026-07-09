"""Tests for GET /api/invitations (SAP extraction trigger)."""



from collections.abc import Generator

from datetime import date

from unittest.mock import patch



import pytest

from fastapi.testclient import TestClient



from app.controllers.invitation_controller import (

    InvitationExtractionError,

    InvitationNotFoundError,

)

from app.main import create_app

from app.schemas.invitation import InvitationCreate





@pytest.fixture

def client() -> Generator[TestClient, None, None]:

    app = create_app()

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





def test_extract_all_invitations_empty(client: TestClient) -> None:

    with patch(

        "app.api.routes.invitations.extract_invitations_via_api",

        return_value=[],

    ):

        response = client.get("/api/invitations")



    assert response.status_code == 200

    body = response.json()

    assert body["data"] == []

    assert body["count"] == 0





def test_extract_all_invitations_with_data(client: TestClient) -> None:

    with patch(

        "app.api.routes.invitations.extract_invitations_via_api",

        return_value=[_sample_invitation()],

    ):

        response = client.get("/api/invitations")



    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 1

    assert body["data"][0]["invitationId"] == "UAE1401324"





def test_extract_invitation_by_valid_id(client: TestClient) -> None:

    with patch(

        "app.api.routes.invitations.extract_invitations_via_api",

        return_value=_sample_invitation(),

    ):

        response = client.get("/api/invitations", params={"invitationId": "UAE1401324"})



    assert response.status_code == 200

    body = response.json()

    assert body["data"]["invitationId"] == "UAE1401324"

    assert body["data"]["customer_ref"] == "2182600106"





def test_extract_invitation_by_invalid_id_format(client: TestClient) -> None:

    response = client.get("/api/invitations", params={"invitationId": "not-valid"})

    assert response.status_code == 400

    assert response.json()["error"] == "Invalid invitationId format"





def test_extract_invitation_not_found(client: TestClient) -> None:

    with patch(

        "app.api.routes.invitations.extract_invitations_via_api",

        side_effect=InvitationNotFoundError("Invitation UAE9999999 not found in search results"),

    ):

        response = client.get("/api/invitations", params={"invitationId": "UAE9999999"})



    assert response.status_code == 404

    assert "not found" in response.json()["error"]





def test_extract_invitation_sap_error(client: TestClient) -> None:

    with patch(

        "app.api.routes.invitations.extract_invitations_via_api",

        side_effect=InvitationExtractionError("Date range is required. Set SCRAPE_DATE_FROM/SCRAPE_DATE_TO in .env."),

    ):

        response = client.get("/api/invitations")



    assert response.status_code == 400

    assert response.json()["error"] == "Date range is required. Set SCRAPE_DATE_FROM/SCRAPE_DATE_TO in .env."


