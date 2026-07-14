"""Invitation extraction service (CLI + API share this)."""

from __future__ import annotations

import logging

from app.clients.database_client import get_database_client, upsert_invitation
from app.configs.settings import Settings, get_settings
from app.controllers.invitation_controllers.sap_invitation_extractor import SapInvitationExtractor
from app.controllers.login_controller import LoginController
from app.controllers.selenuim_client import SapClient, SapClientError
from app.schemas.invitation import (
    InvitationApiItem,
    InvitationCreate,
    InvitationExtractResponse,
    InvitationSingleResponse,
)

logger = logging.getLogger("al_ghanem.extraction.invitations")

INVITATION_MODES = frozenset({"today", "yesterday", "all"})


class InvitationExtractionError(Exception):
    """Raised when invitation extraction cannot run."""


class InvitationNotFoundError(InvitationExtractionError):
    """Raised when the requested invitation ID is not in SAP search results."""


def _normalize_mode(mode: str | None) -> str:
    normalized = (mode or "today").strip().lower()
    if normalized not in INVITATION_MODES:
        raise InvitationExtractionError(
            f"Unsupported mode '{mode}'. Use --mode today|yesterday|all."
        )
    return normalized


def extract_invitations(
    *,
    mode: str = "today",
    headless: bool | None = None,
    settings: Settings | None = None,
    max_count: int | None = None,
) -> int:
    """CLI extraction: scrape SAP for the selected mode and upsert invitations."""
    invitations = extract_invitations_via_api(
        invitation_id=None,
        mode=mode,
        headless=headless,
        settings=settings,
        max_count=max_count,
    )
    return len(invitations)


def extract_invitations_via_api(
    invitation_id: str | None = None,
    *,
    mode: str = "today",
    headless: bool | None = None,
    settings: Settings | None = None,
    max_count: int | None = None,
) -> InvitationCreate | list[InvitationCreate]:
    """
    Run SAP extraction for the API / CLI.

    Modes:
    - today: Document Date = Today (existing behavior)
    - yesterday: Document Date = Yesterday
    - all: no date filter; click Go only

    - With invitation_id: scrape that single invitation from SAP.
    - Without invitation_id: scrape invitations up to max_count
      (None → SAP_MAX_INVITATIONS; 0 → unlimited).
    """
    config = settings or get_settings()
    selected_mode = _normalize_mode(mode)
    limit = config.sap_max_invitations if max_count is None else max_count
    db_client = get_database_client()

    logger.info(
        "Invitation extraction mode=%s (limit=%s)",
        selected_mode,
        limit if limit > 0 else "unlimited",
    )

    try:
        with SapClient(headless=headless, settings=config) as sap_client:
            LoginController(sap_client).login()
            extractor = SapInvitationExtractor(sap_client)
            extractor.prepare_search(mode=selected_mode)

            if invitation_id:
                invitation = extractor.extract_by_ref(invitation_id)
                with db_client.session() as session:
                    upsert_invitation(session, invitation)
                logger.info("Extracted invitation %s via API", invitation.inv_ref)
                return invitation

            results: list[InvitationCreate] = []
            with db_client.session() as session:
                for invitation in extractor.iter_invitations(max_count=limit):
                    upsert_invitation(session, invitation)
                    results.append(invitation)
                    logger.info(
                        "Extracted invitation %s (%s/%s)",
                        invitation.inv_ref,
                        len(results),
                        limit if limit > 0 else "∞",
                    )
    except SapClientError as exc:
        message = str(exc)
        if invitation_id and "not found" in message.lower():
            raise InvitationNotFoundError(message) from exc
        raise InvitationExtractionError(message) from exc

    logger.info("Invitation extraction finished. Extracted %s record(s).", len(results))
    return results


def run_invitation_extraction(
    mode: str,
    invitation_id: str | None = None,
) -> InvitationSingleResponse | InvitationExtractResponse:
    """
    API-oriented extraction: always show the browser (headless=False),
    then map domain results to API response models.

    Raises InvitationNotFoundError / InvitationExtractionError for the routes layer
    to translate into HTTP responses.
    """
    result = extract_invitations_via_api(
        invitation_id=invitation_id,
        mode=mode,
        headless=False,
    )

    if isinstance(result, InvitationCreate):
        return InvitationSingleResponse(data=InvitationApiItem.from_create(result))

    items = [InvitationApiItem.from_create(invitation) for invitation in result]
    return InvitationExtractResponse(mode=mode, data=items, count=len(items))
