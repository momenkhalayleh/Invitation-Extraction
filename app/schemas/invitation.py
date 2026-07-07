from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


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


class InvitationRead(InvitationBase):
    model_config = ConfigDict(from_attributes=True)

    extracted_at: datetime
    updated_at: datetime
