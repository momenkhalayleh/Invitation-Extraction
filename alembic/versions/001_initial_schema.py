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
        "product_type",
        sa.Column("product_type_id", sa.String(length=64), nullable=False),
        sa.Column("product_type_description", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("product_type_id"),
    )

    op.bulk_insert(
        sa.table(
            "product_type",
            sa.column("product_type_id", sa.String),
            sa.column("product_type_description", sa.String),
        ),
        [
            {"product_type_id": "AC", "product_type_description": "Airpack Compressor"},
            {"product_type_id": "AD", "product_type_description": "AC/DC systems"},
            {"product_type_id": "CH", "product_type_description": "Chemicals"},
            {"product_type_id": "CM", "product_type_description": "Compressors"},
            {"product_type_id": "CRCO", "product_type_description": "Crane Maint.Call off Cont"},
            {"product_type_id": "CROT", "product_type_description": "Crane Maint.One-time job"},
            {"product_type_id": "CRSE", "product_type_description": "Crane - Sales - Equipment"},
            {"product_type_id": "CRSP", "product_type_description": "Crane-Sales- Spare Parts"},
            {"product_type_id": "CRWJ", "product_type_description": "Crane Maint. Workshop job"},
            {"product_type_id": "CRYC", "product_type_description": "Crane Maint. Yearly cont."},
            {"product_type_id": "CT", "product_type_description": "Cooling Towers"},
            {"product_type_id": "DN", "product_type_description": "Denora-Water treatment"},
            {"product_type_id": "ED", "product_type_description": "LAB AND EDUCATION"},
            {"product_type_id": "EL", "product_type_description": "Electrical"},
            {"product_type_id": "ERSA", "product_type_description": "Spare Parts"},
            {"product_type_id": "FERT", "product_type_description": "Finished Product"},
            {"product_type_id": "FHMI", "product_type_description": "Production Resource/Tool"},
            {"product_type_id": "FL", "product_type_description": "Flow"},
            {"product_type_id": "FW", "product_type_description": "FLOW II"},
            {"product_type_id": "GRCR", "product_type_description": "GRINDING& CRUSHING"},
            {"product_type_id": "GS", "product_type_description": "Gears Services"},
            {"product_type_id": "HALB", "product_type_description": "Semifinished Product"},
            {"product_type_id": "HAWA", "product_type_description": "Trading Goods"},
            {"product_type_id": "HERS", "product_type_description": "Manufacturer Part"},
            {"product_type_id": "HIBE", "product_type_description": "Operating supplies"},
            {"product_type_id": "IMS", "product_type_description": "Industrial Mech. Services"},
            {"product_type_id": "IN", "product_type_description": "Instrumentation"},
            {"product_type_id": "KMAT", "product_type_description": "Configurable materials"},
            {"product_type_id": "LEIH", "product_type_description": "Returnable packaging"},
            {"product_type_id": "MAT", "product_type_description": "Material general"},
            {"product_type_id": "MCT", "product_type_description": "Machines & Tools"},
            {"product_type_id": "MH", "product_type_description": "Material Handling"},
            {"product_type_id": "MT", "product_type_description": "Material Group"},
            {"product_type_id": "NLAG", "product_type_description": "Non-Stock Material"},
            {"product_type_id": "PG", "product_type_description": "Power Generation"},
            {"product_type_id": "PIPE", "product_type_description": "Pipeline Materials"},
            {"product_type_id": "PRJ", "product_type_description": "Projects"},
            {"product_type_id": "PS", "product_type_description": "Pumps Services"},
            {"product_type_id": "PT", "product_type_description": "Power Transmission"},
            {"product_type_id": "RFR", "product_type_description": "Refractory Services"},
            {"product_type_id": "RJCT", "product_type_description": "Rejected"},
            {"product_type_id": "ROH", "product_type_description": "Raw materials"},
            {"product_type_id": "SBPD", "product_type_description": "Sub. Billing Product"},
            {"product_type_id": "SBRE", "product_type_description": "Sub. Billing Rate Element"},
            {"product_type_id": "SERV", "product_type_description": "Service Product"},
            {"product_type_id": "SF", "product_type_description": "Safety & Fire Fighting"},
            {"product_type_id": "SM", "product_type_description": "SEPARATION & MIXING"},
            {"product_type_id": "SO", "product_type_description": "Solar System"},
            {"product_type_id": "SPI", "product_type_description": "Spare Parts-ISG"},
            {"product_type_id": "TD", "product_type_description": "Transmission&Distribution"},
            {"product_type_id": "TH", "product_type_description": "Thermal System"},
            {"product_type_id": "TRCE", "product_type_description": "deleted"},
            {"product_type_id": "TRCM", "product_type_description": "deleted"},
            {"product_type_id": "TRD", "product_type_description": "Trading"},
            {"product_type_id": "TSCE", "product_type_description": "TSG-Retail/Shr-Const.Eqpt"},
            {"product_type_id": "TSCM", "product_type_description": "TSG-Retail/Shr-Const.Mtrl"},
            {"product_type_id": "TSCO", "product_type_description": "TSG - Maint.Call off Cont"},
            {"product_type_id": "TSCS", "product_type_description": "TSG-Sales-Const.Solution"},
            {"product_type_id": "TSEL", "product_type_description": "TSG - Sales - Electrical"},
            {"product_type_id": "TSME", "product_type_description": "TSG - Sales - Mechanical"},
            {"product_type_id": "TSOT", "product_type_description": "TSG - Maint.One-time job"},
            {"product_type_id": "TSRA", "product_type_description": "TSG-Retail/Shr-Aluminum"},
            {"product_type_id": "TSRC", "product_type_description": "TSG-Retail/Shr-Chemicals"},
            {"product_type_id": "TSRM", "product_type_description": "TSG-Retail/Shr-Machinery"},
            {"product_type_id": "TSSP", "product_type_description": "TSG-Retail/Shr Spare Part"},
            {"product_type_id": "TSSR", "product_type_description": "TSG-Retail/Shr-Services"},
            {"product_type_id": "TSWJ", "product_type_description": "TSG - Maint. Workshop job"},
            {"product_type_id": "TSYC", "product_type_description": "TSG - Maint. Yearly cont."},
            {"product_type_id": "UN...", "product_type_description": "Nonvaluated Material"},
            {"product_type_id": "VERP", "product_type_description": "Packaging"},
            {"product_type_id": "XX1", "product_type_description": "Pricing Conditions"},
            {"product_type_id": "XX2", "product_type_description": "Service Contract Items"},
        ],
    )

    op.create_table(
        "invitations",
        sa.Column("inv_ref", sa.String(length=64), nullable=False),
        sa.Column("customer_ref", sa.String(length=128), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("scope_of_work", sa.Text(), nullable=True),
        sa.Column("inv_subject", sa.String(length=512), nullable=True),
        sa.Column("product_type", sa.String(length=128), nullable=False),
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
        sa.ForeignKeyConstraint(["product_type"], ["product_type.product_type_id"], ondelete="CASCADE"),

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
