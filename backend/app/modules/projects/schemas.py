import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ProjectStatus = Literal["planning", "active", "on_hold", "completed", "cancelled"]
ReportStatus = Literal["draft", "submitted"]
EquipmentStatus = Literal["operating", "idle", "maintenance", "offline"]


class ProjectCreate(BaseModel):
    organization_id: uuid.UUID
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    status: ProjectStatus = "planning"
    currency: str = Field(default="MMK", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    contract_value: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_order(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ProjectUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    status: ProjectStatus | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    contract_value: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_order(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    name: str
    description: str | None
    status: ProjectStatus
    currency: str
    contract_value: Decimal | None
    start_date: date | None
    end_date: date | None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DailySiteReportCreate(BaseModel):
    report_date: date
    shift: str = Field(default="day", min_length=1, max_length=30)
    weather: str | None = Field(default=None, max_length=100)
    headcount: int = Field(default=0, ge=0, le=100000)
    work_completed: str = Field(min_length=1, max_length=20000)
    issues: str | None = Field(default=None, max_length=20000)
    safety_incidents: int = Field(default=0, ge=0, le=10000)


class DailySiteReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    report_date: date
    shift: str
    weather: str | None
    headcount: int
    work_completed: str
    issues: str | None
    safety_incidents: int
    status: ReportStatus
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class WorkforceEntryCreate(BaseModel):
    work_date: date
    shift: str = Field(default="day", min_length=1, max_length=30)
    trade: str = Field(min_length=1, max_length=100)
    contractor: str = Field(default="Direct", min_length=1, max_length=160)
    worker_count: int = Field(ge=0, le=100000)
    hours_per_worker: Decimal = Field(ge=0, le=24, max_digits=5, decimal_places=2)
    notes: str | None = Field(default=None, max_length=10000)


class WorkforceEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    work_date: date
    shift: str
    trade: str
    contractor: str
    worker_count: int
    hours_per_worker: Decimal
    notes: str | None
    author_id: uuid.UUID
    created_at: datetime


class EquipmentUsageCreate(BaseModel):
    work_date: date
    shift: str = Field(default="day", min_length=1, max_length=30)
    equipment_code: str = Field(
        min_length=1, max_length=50, pattern=r"^[A-Za-z0-9._-]+$"
    )
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    location: str | None = Field(default=None, max_length=200)
    status: EquipmentStatus
    operating_hours: Decimal = Field(default=Decimal("0"), ge=0, le=24, max_digits=5, decimal_places=2)
    idle_hours: Decimal = Field(default=Decimal("0"), ge=0, le=24, max_digits=5, decimal_places=2)
    fuel_liters: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=3)
    notes: str | None = Field(default=None, max_length=10000)

    @model_validator(mode="after")
    def validate_shift_hours(self):
        if self.operating_hours + self.idle_hours > 24:
            raise ValueError("operating_hours plus idle_hours cannot exceed 24")
        return self


class EquipmentUsageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    work_date: date
    shift: str
    equipment_code: str
    name: str
    category: str
    location: str | None
    status: EquipmentStatus
    operating_hours: Decimal
    idle_hours: Decimal
    fuel_liters: Decimal
    notes: str | None
    author_id: uuid.UUID
    created_at: datetime


class MaterialUsageCreate(BaseModel):
    work_date: date
    shift: str = Field(default="day", min_length=1, max_length=30)
    material_code: str = Field(
        min_length=1, max_length=50, pattern=r"^[A-Za-z0-9._-]+$"
    )
    name: str = Field(min_length=1, max_length=160)
    unit: str = Field(min_length=1, max_length=30)
    quantity: Decimal = Field(gt=0, max_digits=16, decimal_places=3)
    location: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=10000)


class MaterialUsageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    work_date: date
    shift: str
    material_code: str
    name: str
    unit: str
    quantity: Decimal
    location: str | None
    notes: str | None
    author_id: uuid.UUID
    created_at: datetime
