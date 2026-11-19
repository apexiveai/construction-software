"""Add tenant-scoped projects and daily site reports.

Revision ID: 20261119_01
Revises: c0d56645fb97
Create Date: 2026-11-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261119_01"
down_revision: Union[str, Sequence[str], None] = "c0d56645fb97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="planning", nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="MMK", nullable=False),
        sa.Column("contract_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_project_date_order",
        ),
        sa.CheckConstraint(
            "status IN ('planning', 'active', 'on_hold', 'completed', 'cancelled')",
            name="ck_project_status",
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_project_organization_code"),
    )
    op.create_index(
        "ix_project_organization_status",
        "projects",
        ["organization_id", "status"],
    )

    op.create_table(
        "daily_site_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("shift", sa.String(length=30), server_default="day", nullable=False),
        sa.Column("weather", sa.String(length=100), nullable=True),
        sa.Column("headcount", sa.Integer(), server_default="0", nullable=False),
        sa.Column("work_completed", sa.Text(), nullable=False),
        sa.Column("issues", sa.Text(), nullable=True),
        sa.Column("safety_incidents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("headcount >= 0", name="ck_daily_report_headcount"),
        sa.CheckConstraint("safety_incidents >= 0", name="ck_daily_report_safety_incidents"),
        sa.CheckConstraint("status IN ('draft', 'submitted')", name="ck_daily_report_status"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "report_date",
            "shift",
            name="uq_daily_site_report_project_date_shift",
        ),
    )
    op.create_index(
        "ix_daily_report_project_date",
        "daily_site_reports",
        ["project_id", "report_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_daily_report_project_date", table_name="daily_site_reports")
    op.drop_table("daily_site_reports")
    op.drop_index("ix_project_organization_status", table_name="projects")
    op.drop_table("projects")
