import logging

from app.clients.database_client import get_database_client, upsert_invitation
from app.clients.sap_client import SapClient, SapClientError
from app.clients.sap_invitation_extractor import SapInvitationExtractor
from app.configs.settings import Settings, get_settings

logger = logging.getLogger("al_ghanem.extraction.invitations")


class InvitationExtractionError(Exception):
    """Raised when invitation extraction cannot run."""


def extract_invitations(
    date_from: str | None = None,
    date_to: str | None = None,
    headless: bool | None = None,
    settings: Settings | None = None,
) -> int:
    config = settings or get_settings()
    start_date = date_from or config.scrape_date_from
    end_date = date_to or config.scrape_date_to

    if not start_date or not end_date:
        raise InvitationExtractionError(
            "Date range is required. Set SCRAPE_DATE_FROM/SCRAPE_DATE_TO in .env or pass --from-date/--to-date."
        )

    saved_count = 0
    db_client = get_database_client()

    try:
        with SapClient(headless=headless, settings=config) as sap_client:
            sap_client.login()
            extractor = SapInvitationExtractor(sap_client)
            extractor.prepare_search(start_date, end_date)

            with db_client.session() as session:
                for invitation in extractor.iter_invitations():
                    upsert_invitation(session, invitation)
                    saved_count += 1
                    logger.info("Saved invitation %s (%s total)", invitation.inv_ref, saved_count)
    except SapClientError as exc:
        raise InvitationExtractionError(str(exc)) from exc

    logger.info("Invitation extraction finished. Saved %s record(s).", saved_count)
    return saved_count
