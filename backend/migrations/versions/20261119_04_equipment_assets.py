"""Add an organization-owned equipment asset registry.

Revision ID: 20261119_04
Revises: 20261119_03
Create Date: 2026-11-19
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261119_04"
down_revision: Union[str, Sequence[str], None] = "20261119_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ASSET_PERMISSIONS = (
    (
        "equipment_assets.read",
        "Read equipment assets",
        "View the organization's equipment asset register.",
    ),
    (
        "equipment_assets.create",
        "Create equipment assets",
        "Register equipment assets for the organization.",
    ),
    (
        "equipment_assets.update",
        "Update equipment assets",
        "Update equipment asset details and status.",
    ),
)


def upgrade() -> None:
    op.create_table(
        "equipment_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("asset_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=24), server_default="available", nullable=False),
        sa.Column("current_project_id", sa.Uuid(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("purchased_on", sa.Date(), nullable=True),
        sa.Column("service_due_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('available', 'in_use', 'maintenance', 'out_of_service')",
            name="ck_equipment_asset_status",
        ),
        sa.ForeignKeyConstraint(
            ["current_project_id"],
            ["projects.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "asset_code",
            name="uq_equipment_asset_organization_code",
        ),
    )
    op.create_index(
        "ix_equipment_asset_org_status",
        "equipment_assets",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_equipment_asset_project",
        "equipment_assets",
        ["current_project_id"],
    )

    permission_table = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String(length=150)),
        sa.column("name", sa.String(length=150)),
        sa.column("description", sa.String(length=500)),
    )
    op.bulk_insert(
        permission_table,
        [
            {
                "id": uuid.uuid5(uuid.NAMESPACE_URL, f"apexiveai:permission:{code}"),
                "code": code,
                "name": name,
                "description": description,
            }
            for code, name, description in ASSET_PERMISSIONS
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM permissions WHERE code IN "
        "('equipment_assets.read', 'equipment_assets.create', "
        "'equipment_assets.update')"
    )
    op.drop_index("ix_equipment_asset_project", table_name="equipment_assets")
    op.drop_index("ix_equipment_asset_org_status", table_name="equipment_assets")
    op.drop_table("equipment_assets")
