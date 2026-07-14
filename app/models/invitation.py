from datetime import date, datetime, timezone

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.models.base import Base, TimestampMixin
from app.schemas.invitation import InvitationCreate


class Invitation(Base, TimestampMixin):
    __tablename__ = "invitations"

    inv_ref: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scope_of_work: Mapped[str | None] = mapped_column(Text, nullable=True)
    inv_subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    closing_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    @classmethod
    def upsert(cls, session: Session, data: InvitationCreate) -> "Invitation":
        invitation = session.get(cls, data.inv_ref)
        payload = data.model_dump()

        if invitation is None:
            invitation = cls(**payload)
            session.add(invitation)
            return invitation

        for field, value in payload.items():
            setattr(invitation, field, value)

        invitation.updated_at = datetime.now(timezone.utc)
        return invitation
