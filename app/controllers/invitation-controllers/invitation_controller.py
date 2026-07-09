import logging

from app.clients.database_client import get_database_client
from app.controllers.invitation_repository import upsert_invitation
from app.controllers.selenuim_client import SapClient, SapClientError
from app.controllers.sap_invitation_extractor import SapInvitationExtractor
from app.configs.settings import Settings, get_settings
from app.schemas.invitation import InvitationCreate

logger = logging.getLogger("al_ghanem.extraction.invitations")


class InvitationExtractionError(Exception):
    """Raised when invitation extraction cannot run."""


class InvitationNotFoundError(InvitationExtractionError):
    """Raised when the requested invitation ID is not in SAP search results."""


def _resolve_date_range(
    date_from: str | None,
    date_to: str | None,
    settings: Settings,
) -> tuple[str, str]:
    start_date = date_from or settings.scrape_date_from
    end_date = date_to or settings.scrape_date_to
    if not start_date or not end_date:
        raise InvitationExtractionError(
            "Date range is required. Set SCRAPE_DATE_FROM/SCRAPE_DATE_TO in .env."
        )
    return start_date, end_date


def extract_invitations(
    date_from: str | None = None,
    date_to: str | None = None,
    headless: bool | None = None,
    settings: Settings | None = None,
) -> int:
    """CLI extraction: scrape SAP and upsert all invitations within the configured limit."""
    invitations = extract_invitations_via_api(
        invitation_id=None,
        date_from=date_from,
        date_to=date_to,
        headless=headless,
        settings=settings,
        max_count=None,
    )
    return len(invitations)


def extract_invitations_via_api(
    invitation_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    headless: bool | None = None,
    settings: Settings | None = None,
    max_count: int | None = None,
) -> InvitationCreate | list[InvitationCreate]:
    """
    Run SAP extraction for the API.

    - With invitation_id: scrape that single invitation from SAP.
    - Without invitation_id: scrape all invitations in the date range (max_count=0 means unlimited).
    """
    config = settings or get_settings()
    start_date, end_date = _resolve_date_range(date_from, date_to, config)
    db_client = get_database_client()

    try:
        with SapClient(headless=headless, settings=config) as sap_client:
            sap_client.login()
            extractor = SapInvitationExtractor(sap_client)
            extractor.prepare_search(start_date, end_date)

            if invitation_id:
                invitation = extractor.extract_by_ref(invitation_id)
                with db_client.session() as session:
                    upsert_invitation(session, invitation)
                logger.info("Extracted invitation %s via API", invitation.inv_ref)
                return invitation

            results: list[InvitationCreate] = []
            with db_client.session() as session:
                for invitation in extractor.iter_invitations(max_count=max_count):
                    upsert_invitation(session, invitation)
                    results.append(invitation)
                    logger.info(
                        "Extracted invitation %s (%s total)",
                        invitation.inv_ref,
                        len(results),
                    )
    except SapClientError as exc:
        message = str(exc)
        if invitation_id and "not found" in message.lower():
            raise InvitationNotFoundError(message) from exc
        raise InvitationExtractionError(message) from exc

    logger.info("Invitation extraction finished. Extracted %s record(s).", len(results))
    return results
