import logging

from fastapi import APIRouter, HTTPException, Query

from app.controllers.invitation_controllers import (
    InvitationExtractionError,
    InvitationNotFoundError,
    parse_optional_invitation_id,
    run_invitation_extraction,
)
from app.schemas.invitation import (
    ErrorResponse,
    InvitationExtractResponse,
    InvitationSingleResponse,
)

logger = logging.getLogger("al_ghanem.extraction.api")
router = APIRouter(prefix="/invitations", tags=["invitations"])

_ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


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
    try:
        invitation_id = parse_optional_invitation_id(invitationId)
        return run_invitation_extraction("today", invitation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvitationExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error while extracting invitations (mode=today)")
        raise HTTPException(status_code=500, detail="Internal server error") from None


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
    try:
        invitation_id = parse_optional_invitation_id(invitationId)
        return run_invitation_extraction("yesterday", invitation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvitationExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error while extracting invitations (mode=yesterday)")
        raise HTTPException(status_code=500, detail="Internal server error") from None


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
    try:
        invitation_id = parse_optional_invitation_id(invitationId)
        return run_invitation_extraction("all", invitation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvitationExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error while extracting invitations (mode=all)")
        raise HTTPException(status_code=500, detail="Internal server error") from None
