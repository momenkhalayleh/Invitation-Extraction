from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.case import Case, RfqItem


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
