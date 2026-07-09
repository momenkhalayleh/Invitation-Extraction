import logging

from fastapi import APIRouter, HTTPException, Query

from app.controllers.invitation_controller import (
    InvitationExtractionError,
    InvitationNotFoundError,
    extract_invitations_via_api,
)
from app.schemas.invitation import (
    ErrorResponse,
    InvitationApiItem,
    InvitationCreate,
    InvitationListResponse,
    InvitationSingleResponse,
    is_valid_invitation_id,
    sanitize_invitation_id,
)

logger = logging.getLogger("al_ghanem.extraction.api")
router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.get(
    "",
    response_model=InvitationSingleResponse | InvitationListResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def extract_invitations(
    invitationId: str | None = Query(
        default=None,
        description="SAP Sales Inquiry ID to extract (e.g. UAE1401324). Omit to extract all.",
    ),
) -> InvitationSingleResponse | InvitationListResponse:
    """
    Extract invitation data from SAP.

    - If invitationId is provided: log in to SAP, find that invitation, scrape and return it.
    - If invitationId is omitted: extract all invitations using the script's configured range.
    """
    invitation_id: str | None = None
    if invitationId is not None:
        try:
            invitation_id = sanitize_invitation_id(invitationId)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid invitationId format") from exc

        if not is_valid_invitation_id(invitation_id):
            raise HTTPException(status_code=400, detail="Invalid invitationId format")

    try:
        # Match CLI `--visible`: always show the browser when extraction is triggered via API.
        result = extract_invitations_via_api(
            invitation_id=invitation_id,
            max_count=0,
            headless=False,
        )
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvitationExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error while extracting invitations")
        raise HTTPException(status_code=500, detail="Internal server error") from None

    if isinstance(result, InvitationCreate):
        return InvitationSingleResponse(data=InvitationApiItem.from_create(result))

    items = [InvitationApiItem.from_create(invitation) for invitation in result]
    return InvitationListResponse(data=items, count=len(items))


