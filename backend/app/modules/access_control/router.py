import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.access_control import (
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from app.models.organization import Organization
from app.models.user import OrganizationMembership, User
from app.modules.access_control.schemas import (
    BootstrapRequest,
    PermissionRead,
    RoleAssignments,
    RoleCreate,
    RoleRead,
)
from app.modules.access_control.service import (
    create_standard_roles,
    require_access_management,
    require_active_membership,
)

router = APIRouter(prefix="/organizations", tags=["Organization Access Control"])


def _serialize_roles(db: Session, roles: list[Role]) -> list[RoleRead]:
    if not roles:
        return []

    role_ids = [role.id for role in roles]
    permission_rows = db.execute(
        select(RolePermission.role_id, Permission.code)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id.in_(role_ids))
        .order_by(Permission.code)
    ).all()
    permission_codes: dict[uuid.UUID, list[str]] = {
        role_id: [] for role_id in role_ids
    }
    for role_id, permission_code in permission_rows:
        permission_codes[role_id].append(permission_code)

    return [
        RoleRead(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            permissions=permission_codes[role.id],
        )
        for role in roles
    ]


def _require_permission_manager(
    db: Session,
    organization_id: uuid.UUID,
    current_user: User,
) -> Organization:
    return require_access_management(db, organization_id, current_user)


@router.get(
    "/{organization_id}/access/permissions",
    response_model=list[PermissionRead],
)
def list_permission_catalog(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_active_membership(db, organization_id, current_user.id)
    return list(
        db.scalars(select(Permission).order_by(Permission.code))
    )


@router.post(
    "/{organization_id}/access/bootstrap",
    response_model=list[RoleRead],
)
def bootstrap_organization_access(
    organization_id: uuid.UUID,
    payload: BootstrapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System administrator permission required",
        )
    organization = db.scalar(
        select(Organization)
        .where(
            Organization.id == organization_id,
            Organization.is_active.is_(True),
        )
        .with_for_update()
    )
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    membership = require_active_membership(
        db,
        organization_id,
        payload.initial_admin_user_id,
    )

    roles = create_standard_roles(db, organization_id)
    admin_role = next(role for role in roles if role.code == "organization_admin")
    exists = db.scalar(
        select(MembershipRole.id).where(
            MembershipRole.membership_id == membership.id,
            MembershipRole.role_id == admin_role.id,
        )
    )
    if exists is None:
        db.add(
            MembershipRole(
                membership_id=membership.id,
                role_id=admin_role.id,
            )
        )

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization access roles could not be initialized",
        ) from error
    return _serialize_roles(db, roles)


@router.get("/{organization_id}/access/roles", response_model=list[RoleRead])
def list_organization_roles(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_active_membership(db, organization_id, current_user.id)
    roles = list(
        db.scalars(
            select(Role)
            .where(Role.organization_id == organization_id)
            .order_by(Role.name)
        )
    )
    return _serialize_roles(db, roles)


@router.post(
    "/{organization_id}/access/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_role(
    organization_id: uuid.UUID,
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_permission_manager(db, organization_id, current_user)
    if len(set(payload.permissions)) != len(payload.permissions):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Permission codes must not contain duplicates",
        )

    permissions = list(
        db.scalars(
            select(Permission).where(Permission.code.in_(payload.permissions))
        )
    )
    if {permission.code for permission in permissions} != set(payload.permissions):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more permission codes are not recognized",
        )

    role = Role(
        organization_id=organization_id,
        code=payload.code,
        name=payload.name,
        description=payload.description,
        is_system=False,
    )
    try:
        db.add(role)
        db.flush()
        db.add_all(
            RolePermission(role_id=role.id, permission_id=permission.id)
            for permission in permissions
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A role with this code already exists in the organization",
        ) from error
    db.refresh(role)
    return _serialize_roles(db, [role])[0]


@router.put(
    "/{organization_id}/access/members/{user_id}/roles",
    response_model=list[RoleRead],
)
def replace_member_roles(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: RoleAssignments,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_permission_manager(db, organization_id, current_user)
    organization = db.scalar(
        select(Organization)
        .where(
            Organization.id == organization_id,
            Organization.is_active.is_(True),
        )
        .with_for_update()
    )
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    membership = require_active_membership(db, organization_id, user_id)
    if len(set(payload.role_codes)) != len(payload.role_codes):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role codes must not contain duplicates",
        )

    roles = list(
        db.scalars(
            select(Role).where(
                Role.organization_id == organization_id,
                Role.code.in_(payload.role_codes),
            )
        )
    )
    if {role.code for role in roles} != set(payload.role_codes):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more organization role codes are not recognized",
        )

    has_admin_permission = False
    if roles:
        has_admin_permission = bool(
            db.scalar(
                select(RolePermission.role_id)
                .join(
                    Permission,
                    Permission.id == RolePermission.permission_id,
                )
                .where(
                    RolePermission.role_id.in_([role.id for role in roles]),
                    Permission.code == "access_control.manage",
                )
                .limit(1)
            )
        )
    if not has_admin_permission and not current_user.is_superuser:
        another_manager = db.scalar(
            select(MembershipRole.id)
            .join(
                OrganizationMembership,
                OrganizationMembership.id == MembershipRole.membership_id,
            )
            .join(User, User.id == OrganizationMembership.user_id)
            .join(Role, Role.id == MembershipRole.role_id)
            .join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.status == "active",
                User.is_active.is_(True),
                MembershipRole.membership_id != membership.id,
                Permission.code == "access_control.manage",
            )
            .limit(1)
        )
        if another_manager is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The last organization access manager cannot be removed",
            )

    db.execute(
        delete(MembershipRole).where(
            MembershipRole.membership_id == membership.id
        )
    )
    db.add_all(
        MembershipRole(membership_id=membership.id, role_id=role.id)
        for role in roles
    )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member roles could not be updated",
        ) from error
    return _serialize_roles(db, roles)
