from datetime import datetime, timezone

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
