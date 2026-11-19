import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.modules.projects.models import Project
from app.modules.projects.service import (
    get_accessible_project,
    permitted_organization_ids,
)
from app.modules.quality.models import (
    QualityInspection,
    QualityInspectionDecision,
    QualityInspectionFinding,
)
from app.modules.quality.schemas import (
    QualityInspectionCreate,
    QualityInspectionDecisionCreate,
    QualityInspectionRead,
)

router = APIRouter(prefix="/projects/{project_id}/inspections", tags=["Quality"])


def _require_project_permission(
    db: Session,
    project_id: uuid.UUID,
    current_user: User,
    permission_code: str,
) -> Project:
    project = get_accessible_project(
        db,
        project_id,
        permitted_organization_ids(db, current_user, permission_code),
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def _inspection_query(project_id: uuid.UUID, inspection_id: uuid.UUID):
    return (
        select(QualityInspection)
        .options(
            selectinload(QualityInspection.findings),
            selectinload(QualityInspection.decision),
        )
        .where(
            QualityInspection.project_id == project_id,
            QualityInspection.id == inspection_id,
        )
        .with_for_update()
    )


@router.get("", response_model=list[QualityInspectionRead])
def list_inspections(
    project_id: uuid.UUID,
    status_filter: str | None = Query(default=None, alias="status", max_length=20),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_project_permission(db, project_id, current_user, "quality_inspections.read")
    query = (
        select(QualityInspection)
        .options(
            selectinload(QualityInspection.findings),
            selectinload(QualityInspection.decision),
        )
        .where(QualityInspection.project_id == project_id)
        .order_by(QualityInspection.created_at.desc(), QualityInspection.id)
        .offset(offset)
        .limit(limit)
    )
    if status_filter is not None:
        if status_filter not in {"draft", "submitted", "approved", "rejected"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid inspection status",
            )
        query = query.where(QualityInspection.status == status_filter)
    return list(db.scalars(query))


@router.post(
    "",
    response_model=QualityInspectionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_inspection(
    payload: QualityInspectionCreate,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_project_permission(
        db, project_id, current_user, "quality_inspections.create"
    )
    inspection = QualityInspection(
        project_id=project_id,
        inspection_code=payload.inspection_code,
        title=payload.title,
        inspection_type=payload.inspection_type,
        location=payload.location,
        scheduled_on=payload.scheduled_on,
        created_by_id=current_user.id,
        findings=[
            QualityInspectionFinding(**finding.model_dump())
            for finding in payload.findings
        ],
    )
    db.add(inspection)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An inspection with this code or duplicate finding code already exists",
        ) from error
    db.refresh(inspection)
    return inspection


@router.post(
    "/{inspection_id}/submit",
    response_model=QualityInspectionRead,
)
def submit_inspection(
    inspection_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_project_permission(
        db, project_id, current_user, "quality_inspections.submit"
    )
    inspection = db.scalar(_inspection_query(project_id, inspection_id))
    if inspection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if inspection.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft inspections can be submitted",
        )

    inspection.status = "submitted"
    inspection.submitted_by_id = current_user.id
    inspection.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inspection)
    return inspection


@router.post(
    "/{inspection_id}/decision",
    response_model=QualityInspectionRead,
)
def decide_inspection(
    payload: QualityInspectionDecisionCreate,
    inspection_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_project_permission(
        db, project_id, current_user, "quality_inspections.review"
    )
    inspection = db.scalar(_inspection_query(project_id, inspection_id))
    if inspection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if inspection.status != "submitted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only submitted inspections can be reviewed",
        )
    if current_user.id in {
        inspection.created_by_id,
        inspection.submitted_by_id,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inspectors and submitters cannot review their own inspections",
        )
    if payload.decision == "approved" and any(
        finding.result == "fail" for finding in inspection.findings
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Inspections with failed findings cannot be approved",
        )

    now = datetime.now(timezone.utc)
    inspection.status = payload.decision
    inspection.reviewed_by_id = current_user.id
    inspection.reviewed_at = now
    inspection.decision = QualityInspectionDecision(
        decision=payload.decision,
        reviewer_id=current_user.id,
        comments=payload.comments,
        decided_at=now,
    )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inspection has already been reviewed",
        ) from error
    db.refresh(inspection)
    return inspection
