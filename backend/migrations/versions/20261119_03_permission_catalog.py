"""Seed the core project and site-operation permission catalog.

Revision ID: 20261119_03
Revises: 20261119_02
Create Date: 2026-11-19
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261119_03"
down_revision: Union[str, Sequence[str], None] = "20261119_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = (
    ("projects.read", "Read projects", "View projects in an organization."),
    ("projects.create", "Create projects", "Create projects in an organization."),
    ("projects.update", "Update projects", "Edit projects in an organization."),
    ("site_reports.read", "Read site reports", "View daily site reports."),
    ("site_reports.create", "Create site reports", "Create daily site reports."),
    ("workforce.read", "Read workforce", "View workforce records."),
    ("workforce.create", "Create workforce", "Create workforce records."),
    ("equipment_usage.read", "Read equipment usage", "View daily equipment usage."),
    ("equipment_usage.create", "Create equipment usage", "Create daily equipment usage."),
    ("material_usage.read", "Read material usage", "View material usage records."),
    ("material_usage.create", "Create material usage", "Create material usage records."),
    (
        "access_control.manage",
        "Manage organization access",
        "Create roles and assign them to organization members.",
    ),
)


def upgrade() -> None:
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String(length=150)),
        sa.column("name", sa.String(length=150)),
        sa.column("description", sa.String(length=500)),
    )
    op.bulk_insert(
        permissions,
        [
            {
                "id": uuid.uuid5(uuid.NAMESPACE_URL, f"apexiveai:permission:{code}"),
                "code": code,
                "name": name,
                "description": description,
            }
            for code, name, description in PERMISSIONS
        ],
    )


def downgrade() -> None:
    permission_codes = tuple(code for code, _, _ in PERMISSIONS)
    op.execute(
        sa.text("DELETE FROM permissions WHERE code IN :codes").bindparams(
            sa.bindparam("codes", expanding=True, value=permission_codes)
        )
    )
