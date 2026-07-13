import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.controllers.invitation_controllers import (
    InvitationExtractionError,
    InvitationNotFoundError,
    extract_invitations_via_api,
)
from app.schemas.invitation import (
    ErrorResponse,
    InvitationApiItem,
    InvitationCreate,
    InvitationExtractResponse,
    InvitationSingleResponse,
    is_valid_invitation_id,
    sanitize_invitation_id,
)

logger = logging.getLogger("al_ghanem.extraction.api")
router = APIRouter(prefix="/invitations", tags=["invitations"])

InvitationMode = Literal["today", "yesterday", "all"]

_ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


def _parse_invitation_id(invitation_id: str | None) -> str | None:
    if invitation_id is None:
        return None
    try:
        cleaned = sanitize_invitation_id(invitation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid invitationId format") from exc
    if not is_valid_invitation_id(cleaned):
        raise HTTPException(status_code=400, detail="Invalid invitationId format")
    return cleaned


def _run_extraction(
    mode: InvitationMode,
    invitation_id: str | None,
) -> InvitationSingleResponse | InvitationExtractResponse:
    try:
        # Match CLI `--visible`: show the browser when extraction is triggered via API.
        result = extract_invitations_via_api(
            invitation_id=invitation_id,
            mode=mode,
            headless=False,
        )
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvitationExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error while extracting invitations (mode=%s)", mode)
        raise HTTPException(status_code=500, detail="Internal server error") from None

    if isinstance(result, InvitationCreate):
        return InvitationSingleResponse(data=InvitationApiItem.from_create(result))

    items = [InvitationApiItem.from_create(invitation) for invitation in result]
    return InvitationExtractResponse(mode=mode, data=items, count=len(items))


@router.get(
    "/today",
    response_model=InvitationSingleResponse | InvitationExtractResponse,
    responses=_ERROR_RESPONSES,
)
def extract_invitations_today(
    invitationId: str | None = Query(
        default=None,
        description="Optional SAP Sales Inquiry ID within Today's results.",
    ),
) -> InvitationSingleResponse | InvitationExtractResponse:
    """Extract invitations with Document Date = Today."""
    return _run_extraction("today", _parse_invitation_id(invitationId))


@router.get(
    "/yesterday",
    response_model=InvitationSingleResponse | InvitationExtractResponse,
    responses=_ERROR_RESPONSES,
)
def extract_invitations_yesterday(
    invitationId: str | None = Query(
        default=None,
        description="Optional SAP Sales Inquiry ID within Yesterday's results.",
    ),
) -> InvitationSingleResponse | InvitationExtractResponse:
    """Extract invitations with Document Date = Yesterday."""
    return _run_extraction("yesterday", _parse_invitation_id(invitationId))


@router.get(
    "/all",
    response_model=InvitationSingleResponse | InvitationExtractResponse,
    responses=_ERROR_RESPONSES,
)
def extract_invitations_all(
    invitationId: str | None = Query(
        default=None,
        description="Optional SAP Sales Inquiry ID within unfiltered (Go only) results.",
    ),
) -> InvitationSingleResponse | InvitationExtractResponse:
    """Extract invitations with no Document Date filter (Go only)."""
    return _run_extraction("all", _parse_invitation_id(invitationId))
