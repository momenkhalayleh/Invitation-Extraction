from datetime import date, datetime, timezone

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

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

    cases: Mapped[list["Case"]] = relationship(back_populates="invitation")
    rfq_items: Mapped[list["RfqItem"]] = relationship(back_populates="invitation")

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


class Case(Base, TimestampMixin):
    """Case registration record. Overview fields stored in overview_data until layout is finalized."""

    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_ref: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    inv_ref: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("invitations.inv_ref", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overview_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    invitation: Mapped["Invitation"] = relationship(back_populates="cases")
    rfq_items: Mapped[list["RfqItem"]] = relationship(back_populates="case")


class RfqItem(Base, TimestampMixin):
    """External / RFQ line item linked to a case and invitation."""

    __tablename__ = "rfq_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inv_ref: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("invitations.inv_ref", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    invitation: Mapped["Invitation"] = relationship(back_populates="rfq_items")
    case: Mapped["Case"] = relationship(back_populates="rfq_items")
