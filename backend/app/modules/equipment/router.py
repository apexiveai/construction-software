import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.modules.equipment.models import EquipmentAsset
from app.modules.equipment.schemas import (
    EquipmentAssetCreate,
    EquipmentAssetRead,
    EquipmentAssetUpdate,
)
from app.modules.projects.models import Project
from app.modules.projects.service import has_organization_permission

router = APIRouter(
    prefix="/organizations/{organization_id}/equipment-assets",
    tags=["Equipment Asset Registry"],
)


def _require_asset_permission(
    db: Session,
    organization_id: uuid.UUID,
    current_user: User,
    permission_code: str,
) -> None:
    organization = db.scalar(
        select(Organization.id).where(
            Organization.id == organization_id,
            Organization.is_active.is_(True),
        )
    )
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    if not has_organization_permission(
        db,
        current_user,
        organization_id,
        permission_code,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{permission_code} permission required",
        )


def _validate_project_assignment(
    db: Session,
    organization_id: uuid.UUID,
    project_id: uuid.UUID | None,
) -> None:
    if project_id is None:
        return
    project_exists = db.scalar(
        select(Project.id).where(
            Project.id == project_id,
            Project.organization_id == organization_id,
        )
    )
    if project_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this organization",
        )


@router.get("", response_model=list[EquipmentAssetRead])
def list_equipment_assets(
    organization_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    asset_status: str | None = Query(
        default=None,
        alias="status",
        pattern=r"^(available|in_use|maintenance|out_of_service)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_asset_permission(
        db,
        organization_id,
        current_user,
        "equipment_assets.read",
    )
    statement = select(EquipmentAsset).where(
        EquipmentAsset.organization_id == organization_id
    )
    if asset_status is not None:
        statement = statement.where(EquipmentAsset.status == asset_status)
    return list(
        db.scalars(
            statement.order_by(EquipmentAsset.asset_code)
            .offset(offset)
            .limit(limit)
        )
    )


@router.post(
    "",
    response_model=EquipmentAssetRead,
    status_code=status.HTTP_201_CREATED,
)
def create_equipment_asset(
    organization_id: uuid.UUID,
    payload: EquipmentAssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_asset_permission(
        db,
        organization_id,
        current_user,
        "equipment_assets.create",
    )
    _validate_project_assignment(
        db,
        organization_id,
        payload.current_project_id,
    )
    asset = EquipmentAsset(
        organization_id=organization_id,
        **payload.model_dump(),
    )
    db.add(asset)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An asset with this code already exists in the organization",
        ) from error
    db.refresh(asset)
    return asset


@router.patch("/{asset_id}", response_model=EquipmentAssetRead)
def update_equipment_asset(
    organization_id: uuid.UUID,
    asset_id: uuid.UUID,
    payload: EquipmentAssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_asset_permission(
        db,
        organization_id,
        current_user,
        "equipment_assets.update",
    )
    asset = db.scalar(
        select(EquipmentAsset).where(
            EquipmentAsset.id == asset_id,
            EquipmentAsset.organization_id == organization_id,
        )
    )
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment asset not found",
        )

    changes = payload.model_dump(exclude_unset=True)
    project_id = changes.get("current_project_id", asset.current_project_id)
    _validate_project_assignment(db, organization_id, project_id)
    purchased_on = changes.get("purchased_on", asset.purchased_on)
    service_due_on = changes.get("service_due_on", asset.service_due_on)
    if purchased_on and service_due_on and service_due_on < purchased_on:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="service_due_on must not precede purchased_on",
        )
    for field, value in changes.items():
        setattr(asset, field, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An asset with this code already exists in the organization",
        ) from error
    db.refresh(asset)
    return asset
