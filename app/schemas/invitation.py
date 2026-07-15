from datetime import date, datetime, timezone

from pydantic import BaseModel, Field


class InvitationBase(BaseModel):
    inv_ref: str = Field(..., max_length=64)
    customer_ref: str | None = Field(default=None, max_length=128)
    customer_name: str | None = Field(default=None, max_length=255)
    scope_of_work: str | None = None
    inv_subject: str | None = Field(default=None, max_length=512)
    product_type: str | None = Field(default=None, max_length=128)
    closing_date: date | None = None


class InvitationCreate(InvitationBase):
    pass


class InvitationApiItem(BaseModel):
    """Invitation as returned by the HTTP API (invitationId maps from inv_ref)."""

    invitationId: str
    customer_ref: str | None = None
    customer_name: str | None = None
    scope_of_work: str | None = None
    inv_subject: str | None = None
    product_type: str | None = None
    closing_date: date | None = None
    extracted_at: datetime
    updated_at: datetime

    @classmethod
    def from_create(cls, invitation: InvitationCreate) -> "InvitationApiItem":
        now = datetime.now(timezone.utc)
        return cls(
            invitationId=invitation.inv_ref,
            customer_ref=invitation.customer_ref,
            customer_name=invitation.customer_name,
            scope_of_work=invitation.scope_of_work,
            inv_subject=invitation.inv_subject,
            product_type=invitation.product_type,
            closing_date=invitation.closing_date,
            extracted_at=now,
            updated_at=now,
        )


class InvitationSingleResponse(BaseModel):
    data: InvitationApiItem


class InvitationListResponse(BaseModel):
    data: list[InvitationApiItem]
    count: int


class InvitationExtractResponse(BaseModel):
    """List response for mode-based extraction endpoints."""

    mode: str
    data: list[InvitationApiItem]
    count: int


class ErrorResponse(BaseModel):
    error: str
