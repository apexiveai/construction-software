import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AssetStatus = Literal[
    "available",
    "in_use",
    "maintenance",
    "out_of_service",
]


class EquipmentAssetCreate(BaseModel):
    asset_code: str = Field(
        min_length=1, max_length=50, pattern=r"^[A-Za-z0-9._-]+$"
    )
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    serial_number: str | None = Field(default=None, max_length=100)
    status: AssetStatus = "available"
    current_project_id: uuid.UUID | None = None
    location: str | None = Field(default=None, max_length=200)
    purchased_on: date | None = None
    service_due_on: date | None = None

    @model_validator(mode="after")
    def validate_service_date(self):
        if (
            self.purchased_on
            and self.service_due_on
            and self.service_due_on < self.purchased_on
        ):
            raise ValueError("service_due_on must not precede purchased_on")
        return self


class EquipmentAssetUpdate(BaseModel):
    asset_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9._-]+$",
    )
    name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    serial_number: str | None = Field(default=None, max_length=100)
    status: AssetStatus | None = None
    current_project_id: uuid.UUID | None = None
    location: str | None = Field(default=None, max_length=200)
    purchased_on: date | None = None
    service_due_on: date | None = None

    @model_validator(mode="after")
    def require_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class EquipmentAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    asset_code: str
    name: str
    category: str
    serial_number: str | None
    status: AssetStatus
    current_project_id: uuid.UUID | None
    location: str | None
    purchased_on: date | None
    service_due_on: date | None
    created_at: datetime
    updated_at: datetime
