from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Invitation
from app.schemas.invitation import InvitationCreate


def upsert_invitation(session: Session, data: InvitationCreate) -> Invitation:
    invitation = session.get(Invitation, data.inv_ref)
    payload = data.model_dump()

    if invitation is None:
        invitation = Invitation(**payload)
        session.add(invitation)
        return invitation

    for field, value in payload.items():
        setattr(invitation, field, value)

    invitation.updated_at = datetime.now(timezone.utc)
    return invitation


def get_invitation_by_ref(session: Session, inv_ref: str) -> Invitation | None:
    """Fetch a single invitation by Sales Inquiry ID (inv_ref)."""
    return session.get(Invitation, inv_ref)


def list_invitations(session: Session, offset: int = 0, limit: int = 50) -> list[Invitation]:
    """Return a paginated list of invitations ordered by inv_ref."""
    stmt = select(Invitation).order_by(Invitation.inv_ref).offset(offset).limit(limit)
    return list(session.scalars(stmt).all())


def count_invitations(session: Session) -> int:
    """Return total number of invitations in the database."""
    return session.scalar(select(func.count()).select_from(Invitation)) or 0
