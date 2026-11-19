"""Add daily workforce, equipment, and material usage records.

Revision ID: 20261119_02
Revises: 20261119_01
Create Date: 2026-11-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261119_02"
down_revision: Union[str, Sequence[str], None] = "20261119_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workforce_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("shift", sa.String(length=30), server_default="day", nullable=False),
        sa.Column("trade", sa.String(length=100), nullable=False),
        sa.Column("contractor", sa.String(length=160), server_default="Direct", nullable=False),
        sa.Column("worker_count", sa.Integer(), nullable=False),
        sa.Column("hours_per_worker", sa.Numeric(5, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("worker_count >= 0", name="ck_workforce_worker_count"),
        sa.CheckConstraint(
            "hours_per_worker >= 0 AND hours_per_worker <= 24",
            name="ck_workforce_hours_per_worker",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "work_date",
            "shift",
            "trade",
            "contractor",
            name="uq_workforce_project_date_shift_trade_contractor",
        ),
    )
    op.create_index(
        "ix_workforce_project_date",
        "workforce_entries",
        ["project_id", "work_date"],
    )

    op.create_table(
        "equipment_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("shift", sa.String(length=30), server_default="day", nullable=False),
        sa.Column("equipment_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("operating_hours", sa.Numeric(5, 2), server_default="0", nullable=False),
        sa.Column("idle_hours", sa.Numeric(5, 2), server_default="0", nullable=False),
        sa.Column("fuel_liters", sa.Numeric(12, 3), server_default="0", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "operating_hours >= 0 AND operating_hours <= 24",
            name="ck_equipment_operating_hours",
        ),
        sa.CheckConstraint(
            "idle_hours >= 0 AND idle_hours <= 24",
            name="ck_equipment_idle_hours",
        ),
        sa.CheckConstraint(
            "operating_hours + idle_hours <= 24",
            name="ck_equipment_total_shift_hours",
        ),
        sa.CheckConstraint("fuel_liters >= 0", name="ck_equipment_fuel_liters"),
        sa.CheckConstraint(
            "status IN ('operating', 'idle', 'maintenance', 'offline')",
            name="ck_equipment_usage_status",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "work_date",
            "shift",
            "equipment_code",
            name="uq_equipment_usage_project_date_shift_code",
        ),
    )
    op.create_index(
        "ix_equipment_usage_project_date",
        "equipment_usage",
        ["project_id", "work_date"],
    )

    op.create_table(
        "material_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("shift", sa.String(length=30), server_default="day", nullable=False),
        sa.Column("material_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Numeric(16, 3), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_material_usage_quantity"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_material_usage_project_date",
        "material_usage",
        ["project_id", "work_date"],
    )
    op.create_index(
        "ix_material_usage_project_code_date",
        "material_usage",
        ["project_id", "material_code", "work_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_material_usage_project_code_date", table_name="material_usage")
    op.drop_index("ix_material_usage_project_date", table_name="material_usage")
    op.drop_table("material_usage")
    op.drop_index("ix_equipment_usage_project_date", table_name="equipment_usage")
    op.drop_table("equipment_usage")
    op.drop_index("ix_workforce_project_date", table_name="workforce_entries")
    op.drop_table("workforce_entries")
