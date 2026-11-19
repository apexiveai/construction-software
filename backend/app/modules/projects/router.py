import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.modules.projects.models import (
    DailySiteReport,
    EquipmentUsage,
    MaterialUsage,
    Project,
    WorkforceEntry,
)
from app.modules.projects.schemas import (
    DailySiteReportCreate,
    DailySiteReportRead,
    EquipmentUsageCreate,
    EquipmentUsageRead,
    MaterialUsageCreate,
    MaterialUsageRead,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    WorkforceEntryCreate,
    WorkforceEntryRead,
)
from app.modules.projects.service import (
    active_organization_ids,
    get_accessible_project,
    has_organization_permission,
    permitted_organization_ids,
)

router = APIRouter(prefix="/projects", tags=["Projects and Site Operations"])


def _require_accessible_project(
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


@router.get("", response_model=list[ProjectRead])
def list_projects(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization_ids = permitted_organization_ids(
        db, current_user, "projects.read"
    )
    if not organization_ids:
        return []

    return list(
        db.scalars(
            select(Project)
            .where(Project.organization_id.in_(organization_ids))
            .order_by(Project.created_at.desc(), Project.id)
            .offset(offset)
            .limit(limit)
        )
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization_ids = active_organization_ids(db, current_user)
    if payload.organization_id not in organization_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    if not has_organization_permission(
        db,
        current_user,
        payload.organization_id,
        "projects.create",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project creation permission required",
        )

    project = Project(
        **payload.model_dump(),
        created_by_id=current_user.id,
    )
    db.add(project)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with this code already exists in the organization",
        ) from error
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_accessible_project(
        db,
        project_id,
        permitted_organization_ids(db, current_user, "projects.read"),
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_accessible_project(
        db,
        project_id,
        permitted_organization_ids(db, current_user, "projects.update"),
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    changes = payload.model_dump(exclude_unset=True)
    start_date = changes.get("start_date", project.start_date)
    end_date = changes.get("end_date", project.end_date)
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be on or after start_date",
        )

    for field, value in changes.items():
        setattr(project, field, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with this code already exists in the organization",
        ) from error
    db.refresh(project)
    return project


@router.get(
    "/{project_id}/daily-reports",
    response_model=list[DailySiteReportRead],
)
def list_daily_reports(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_accessible_project(
        db,
        project_id,
        permitted_organization_ids(db, current_user, "site_reports.read"),
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return list(
        db.scalars(
            select(DailySiteReport)
            .where(DailySiteReport.project_id == project.id)
            .order_by(
                DailySiteReport.report_date.desc(),
                DailySiteReport.shift,
            )
            .offset(offset)
            .limit(limit)
        )
    )


@router.post(
    "/{project_id}/daily-reports",
    response_model=DailySiteReportRead,
    status_code=status.HTTP_201_CREATED,
)
def create_daily_report(
    project_id: uuid.UUID,
    payload: DailySiteReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_accessible_project(
        db,
        project_id,
        permitted_organization_ids(db, current_user, "site_reports.create"),
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    report = DailySiteReport(
        project_id=project.id,
        author_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(report)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A report already exists for this project, date, and shift",
        ) from error
    db.refresh(report)
    return report


@router.get(
    "/{project_id}/workforce",
    response_model=list[WorkforceEntryRead],
)
def list_workforce_entries(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _require_accessible_project(
        db, project_id, current_user, "workforce.read"
    )
    return list(
        db.scalars(
            select(WorkforceEntry)
            .where(WorkforceEntry.project_id == project.id)
            .order_by(WorkforceEntry.work_date.desc(), WorkforceEntry.shift)
            .offset(offset)
            .limit(limit)
        )
    )


@router.post(
    "/{project_id}/workforce",
    response_model=WorkforceEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workforce_entry(
    project_id: uuid.UUID,
    payload: WorkforceEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _require_accessible_project(
        db, project_id, current_user, "workforce.create"
    )
    entry = WorkforceEntry(
        project_id=project.id,
        author_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(entry)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A workforce entry already exists for this project, date, shift, trade, and contractor",
        ) from error
    db.refresh(entry)
    return entry


@router.get(
    "/{project_id}/equipment-usage",
    response_model=list[EquipmentUsageRead],
)
def list_equipment_usage(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _require_accessible_project(
        db, project_id, current_user, "equipment_usage.read"
    )
    return list(
        db.scalars(
            select(EquipmentUsage)
            .where(EquipmentUsage.project_id == project.id)
            .order_by(EquipmentUsage.work_date.desc(), EquipmentUsage.shift)
            .offset(offset)
            .limit(limit)
        )
    )


@router.post(
    "/{project_id}/equipment-usage",
    response_model=EquipmentUsageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_equipment_usage(
    project_id: uuid.UUID,
    payload: EquipmentUsageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _require_accessible_project(
        db, project_id, current_user, "equipment_usage.create"
    )
    entry = EquipmentUsage(
        project_id=project.id,
        author_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(entry)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An equipment usage entry already exists for this project, date, shift, and equipment code",
        ) from error
    db.refresh(entry)
    return entry


@router.get(
    "/{project_id}/material-usage",
    response_model=list[MaterialUsageRead],
)
def list_material_usage(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _require_accessible_project(
        db, project_id, current_user, "material_usage.read"
    )
    return list(
        db.scalars(
            select(MaterialUsage)
            .where(MaterialUsage.project_id == project.id)
            .order_by(MaterialUsage.work_date.desc(), MaterialUsage.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    )


@router.post(
    "/{project_id}/material-usage",
    response_model=MaterialUsageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_material_usage(
    project_id: uuid.UUID,
    payload: MaterialUsageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _require_accessible_project(
        db, project_id, current_user, "material_usage.create"
    )
    entry = MaterialUsage(
        project_id=project.id,
        author_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
