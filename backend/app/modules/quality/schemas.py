from datetime import date, datetime
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class QualityInspectionFindingCreate(BaseModel):
    finding_code: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=2000)
    result: Literal["pass", "fail", "not_applicable"]
    severity: Literal["minor", "major", "critical"] | None = None
    corrective_action: str | None = Field(default=None, max_length=2000)

    @field_validator("finding_code", "description", "corrective_action")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Text must not be blank")
        return value

    @model_validator(mode="after")
    def require_failed_finding_action(self):
        if self.result == "fail" and (
            self.severity is None or self.corrective_action is None
        ):
            raise ValueError(
                "Failed findings require a severity and corrective action"
            )
        return self


class QualityInspectionCreate(BaseModel):
    inspection_code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    inspection_type: str = Field(min_length=1, max_length=80)
    location: str = Field(min_length=1, max_length=200)
    scheduled_on: date | None = None
    findings: list[QualityInspectionFindingCreate] = Field(min_length=1, max_length=100)

    @field_validator("inspection_code", "title", "inspection_type", "location")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Text must not be blank")
        return value


class QualityInspectionFindingRead(QualityInspectionFindingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class QualityInspectionDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    decision: Literal["approved", "rejected"]
    reviewer_id: uuid.UUID
    comments: str | None
    decided_at: datetime


class QualityInspectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    inspection_code: str
    title: str
    inspection_type: str
    location: str
    scheduled_on: date | None
    status: Literal["draft", "submitted", "approved", "rejected"]
    created_by_id: uuid.UUID
    submitted_by_id: uuid.UUID | None
    submitted_at: datetime | None
    reviewed_by_id: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    findings: list[QualityInspectionFindingRead]
    decision: QualityInspectionDecisionRead | None


class QualityInspectionDecisionCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    comments: str | None = Field(default=None, max_length=2000)

    @field_validator("comments")
    @classmethod
    def trim_comments(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def require_rejection_reason(self):
        if self.decision == "rejected" and not self.comments:
            raise ValueError("A rejection reason is required")
        return self
