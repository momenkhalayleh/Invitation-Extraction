"""Initial schema: invitations, cases, rfq_items

Revision ID: 001
Revises:
Create Date: 2026-07-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invitations",
        sa.Column("inv_ref", sa.String(length=64), nullable=False),
        sa.Column("customer_ref", sa.String(length=128), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("scope_of_work", sa.Text(), nullable=True),
        sa.Column("inv_subject", sa.String(length=512), nullable=True),
        sa.Column("product_type", sa.String(length=128), nullable=True),
        sa.Column("closing_date", sa.Date(), nullable=True),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("inv_ref"),
    )

    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_ref", sa.String(length=64), nullable=False),
        sa.Column("inv_ref", sa.String(length=64), nullable=False),
        sa.Column(
            "overview_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["inv_ref"], ["invitations.inv_ref"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_ref"),
    )
    op.create_index(op.f("ix_cases_inv_ref"), "cases", ["inv_ref"], unique=False)

    op.create_table(
        "rfq_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inv_ref", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column(
            "item_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inv_ref"], ["invitations.inv_ref"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rfq_items_case_id"), "rfq_items", ["case_id"], unique=False)
    op.create_index(op.f("ix_rfq_items_inv_ref"), "rfq_items", ["inv_ref"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rfq_items_inv_ref"), table_name="rfq_items")
    op.drop_index(op.f("ix_rfq_items_case_id"), table_name="rfq_items")
    op.drop_table("rfq_items")
    op.drop_index(op.f("ix_cases_inv_ref"), table_name="cases")
    op.drop_table("cases")
    op.drop_table("invitations")
