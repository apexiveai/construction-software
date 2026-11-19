"""Add inspection findings and independent approval workflow.

Revision ID: 20261119_05
Revises: 20261119_04
Create Date: 2026-11-19
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261119_05"
down_revision: Union[str, Sequence[str], None] = "20261119_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


QUALITY_PERMISSIONS = (
    (
        "quality_inspections.read",
        "Read quality inspections",
        "View inspection records and decisions.",
    ),
    (
        "quality_inspections.create",
        "Create quality inspections",
        "Create inspection records and findings.",
    ),
    (
        "quality_inspections.submit",
        "Submit quality inspections",
        "Submit inspections for independent review.",
    ),
    (
        "quality_inspections.review",
        "Review quality inspections",
        "Approve or reject submitted inspections.",
    ),
)


def upgrade() -> None:
    op.create_table(
        "quality_inspections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("inspection_code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("inspection_type", sa.String(length=80), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("scheduled_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("submitted_by_id", sa.Uuid(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
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
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'approved', 'rejected')",
            name="ck_quality_inspection_status",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "inspection_code",
            name="uq_quality_inspection_project_code",
        ),
    )
    op.create_index(
        "ix_quality_inspection_project_status_date",
        "quality_inspections",
        ["project_id", "status", "scheduled_on"],
    )

    op.create_table(
        "quality_inspection_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("inspection_id", sa.Uuid(), nullable=False),
        sa.Column("finding_code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "result IN ('pass', 'fail', 'not_applicable')",
            name="ck_quality_finding_result",
        ),
        sa.CheckConstraint(
            "severity IS NULL OR severity IN ('minor', 'major', 'critical')",
            name="ck_quality_finding_severity",
        ),
        sa.CheckConstraint(
            "result <> 'fail' OR "
            "(severity IS NOT NULL AND corrective_action IS NOT NULL)",
            name="ck_quality_finding_failed_action",
        ),
        sa.ForeignKeyConstraint(
            ["inspection_id"],
            ["quality_inspections.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "inspection_id",
            "finding_code",
            name="uq_quality_finding_inspection_code",
        ),
    )
    op.create_index(
        "ix_quality_finding_inspection",
        "quality_inspection_findings",
        ["inspection_id"],
    )

    op.create_table(
        "quality_inspection_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("inspection_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "decision IN ('approved', 'rejected')",
            name="ck_quality_inspection_decision",
        ),
        sa.ForeignKeyConstraint(
            ["inspection_id"],
            ["quality_inspections.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "inspection_id",
            name="uq_quality_inspection_decision",
        ),
    )
    op.create_index(
        "ix_quality_decision_reviewer",
        "quality_inspection_decisions",
        ["reviewer_id"],
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
            for code, name, description in QUALITY_PERMISSIONS
        ],
    )

    permission_codes = tuple(code for code, _, _ in QUALITY_PERMISSIONS)
    op.execute(
        sa.text(
            """
            INSERT INTO role_permissions (id, role_id, permission_id)
            SELECT CAST(md5(r.id::text || ':' || p.id::text) AS uuid),
                   r.id,
                   p.id
            FROM roles AS r
            JOIN permissions AS p ON
                (r.code IN ('organization_admin', 'project_manager')
                    AND p.code IN :all_codes)
                OR (r.code = 'site_manager' AND p.code IN :site_codes)
                OR (r.code = 'viewer' AND p.code = 'quality_inspections.read')
            WHERE r.is_system = true
              AND NOT EXISTS (
                  SELECT 1
                  FROM role_permissions AS existing
                  WHERE existing.role_id = r.id
                    AND existing.permission_id = p.id
              )
            """
        ).bindparams(
            sa.bindparam("all_codes", expanding=True, value=permission_codes),
            sa.bindparam(
                "site_codes",
                expanding=True,
                value=(
                    "quality_inspections.read",
                    "quality_inspections.create",
                    "quality_inspections.submit",
                ),
            ),
        )
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM role_permissions WHERE permission_id IN "
        "(SELECT id FROM permissions WHERE code LIKE 'quality_inspections.%')"
    )
    op.execute("DELETE FROM permissions WHERE code LIKE 'quality_inspections.%'")
    op.drop_index(
        "ix_quality_decision_reviewer",
        table_name="quality_inspection_decisions",
    )
    op.drop_table("quality_inspection_decisions")
    op.drop_index(
        "ix_quality_finding_inspection",
        table_name="quality_inspection_findings",
    )
    op.drop_table("quality_inspection_findings")
    op.drop_index(
        "ix_quality_inspection_project_status_date",
        table_name="quality_inspections",
    )
    op.drop_table("quality_inspections")
