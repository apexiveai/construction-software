import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "code",
            name="uq_project_organization_code",
        ),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_project_date_order",
        ),
        CheckConstraint(
            "status IN ('planning', 'active', 'on_hold', 'completed', 'cancelled')",
            name="ck_project_status",
        ),
        Index("ix_project_organization_status", "organization_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="planning", server_default="planning"
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="MMK", server_default="MMK"
    )
    contract_value: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
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


class DailySiteReport(Base):
    __tablename__ = "daily_site_reports"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "report_date",
            "shift",
            name="uq_daily_site_report_project_date_shift",
        ),
        CheckConstraint("headcount >= 0", name="ck_daily_report_headcount"),
        CheckConstraint(
            "safety_incidents >= 0", name="ck_daily_report_safety_incidents"
        ),
        CheckConstraint(
            "status IN ('draft', 'submitted')",
            name="ck_daily_report_status",
        ),
        Index("ix_daily_report_project_date", "project_id", "report_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift: Mapped[str] = mapped_column(
        String(30), nullable=False, default="day", server_default="day"
    )
    weather: Mapped[str | None] = mapped_column(String(100), nullable=True)
    headcount: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    work_completed: Mapped[str] = mapped_column(Text, nullable=False)
    issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_incidents: Mapped[int] = mapped_column(
        nullable=False, default=0, server_default="0"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft"
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
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


class WorkforceEntry(Base):
    __tablename__ = "workforce_entries"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "work_date",
            "shift",
            "trade",
            "contractor",
            name="uq_workforce_project_date_shift_trade_contractor",
        ),
        CheckConstraint("worker_count >= 0", name="ck_workforce_worker_count"),
        CheckConstraint(
            "hours_per_worker >= 0 AND hours_per_worker <= 24",
            name="ck_workforce_hours_per_worker",
        ),
        Index("ix_workforce_project_date", "project_id", "work_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift: Mapped[str] = mapped_column(
        String(30), nullable=False, default="day", server_default="day"
    )
    trade: Mapped[str] = mapped_column(String(100), nullable=False)
    contractor: Mapped[str] = mapped_column(
        String(160), nullable=False, default="Direct", server_default="Direct"
    )
    worker_count: Mapped[int] = mapped_column(nullable=False)
    hours_per_worker: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EquipmentUsage(Base):
    __tablename__ = "equipment_usage"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "work_date",
            "shift",
            "equipment_code",
            name="uq_equipment_usage_project_date_shift_code",
        ),
        CheckConstraint(
            "operating_hours >= 0 AND operating_hours <= 24",
            name="ck_equipment_operating_hours",
        ),
        CheckConstraint(
            "idle_hours >= 0 AND idle_hours <= 24",
            name="ck_equipment_idle_hours",
        ),
        CheckConstraint(
            "operating_hours + idle_hours <= 24",
            name="ck_equipment_total_shift_hours",
        ),
        CheckConstraint("fuel_liters >= 0", name="ck_equipment_fuel_liters"),
        CheckConstraint(
            "status IN ('operating', 'idle', 'maintenance', 'offline')",
            name="ck_equipment_usage_status",
        ),
        Index("ix_equipment_usage_project_date", "project_id", "work_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift: Mapped[str] = mapped_column(
        String(30), nullable=False, default="day", server_default="day"
    )
    equipment_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    operating_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0, server_default="0"
    )
    idle_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0, server_default="0"
    )
    fuel_liters: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=0, server_default="0"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MaterialUsage(Base):
    __tablename__ = "material_usage"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_material_usage_quantity"),
        Index("ix_material_usage_project_date", "project_id", "work_date"),
        Index("ix_material_usage_project_code_date", "project_id", "material_code", "work_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift: Mapped[str] = mapped_column(
        String(30), nullable=False, default="day", server_default="day"
    )
    material_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(16, 3), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
