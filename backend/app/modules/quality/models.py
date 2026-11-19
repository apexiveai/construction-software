import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QualityInspection(Base):
    __tablename__ = "quality_inspections"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "inspection_code",
            name="uq_quality_inspection_project_code",
        ),
        CheckConstraint(
            "status IN ('draft', 'submitted', 'approved', 'rejected')",
            name="ck_quality_inspection_status",
        ),
        Index(
            "ix_quality_inspection_project_status_date",
            "project_id",
            "status",
            "scheduled_on",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    inspection_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    inspection_type: Mapped[str] = mapped_column(String(80), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft"
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    submitted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    findings: Mapped[list["QualityInspectionFinding"]] = relationship(
        back_populates="inspection",
        cascade="all, delete-orphan",
        order_by="QualityInspectionFinding.created_at",
    )
    decision: Mapped["QualityInspectionDecision | None"] = relationship(
        back_populates="inspection",
        cascade="all, delete-orphan",
        uselist=False,
    )


class QualityInspectionFinding(Base):
    __tablename__ = "quality_inspection_findings"
    __table_args__ = (
        UniqueConstraint(
            "inspection_id",
            "finding_code",
            name="uq_quality_finding_inspection_code",
        ),
        CheckConstraint(
            "result IN ('pass', 'fail', 'not_applicable')",
            name="ck_quality_finding_result",
        ),
        CheckConstraint(
            "severity IS NULL OR severity IN ('minor', 'major', 'critical')",
            name="ck_quality_finding_severity",
        ),
        CheckConstraint(
            "result <> 'fail' OR "
            "(severity IS NOT NULL AND corrective_action IS NOT NULL)",
            name="ck_quality_finding_failed_action",
        ),
        Index("ix_quality_finding_inspection", "inspection_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quality_inspections.id", ondelete="CASCADE"),
        nullable=False,
    )
    finding_code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    inspection: Mapped[QualityInspection] = relationship(back_populates="findings")


class QualityInspectionDecision(Base):
    __tablename__ = "quality_inspection_decisions"
    __table_args__ = (
        UniqueConstraint(
            "inspection_id",
            name="uq_quality_inspection_decision",
        ),
        CheckConstraint(
            "decision IN ('approved', 'rejected')",
            name="ck_quality_inspection_decision",
        ),
        Index("ix_quality_decision_reviewer", "reviewer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quality_inspections.id", ondelete="CASCADE"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    inspection: Mapped[QualityInspection] = relationship(back_populates="decision")
