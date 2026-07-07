from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.invitation import Invitation


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
