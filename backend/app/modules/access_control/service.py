import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import PERMISSIONS, ROLE_TEMPLATES
from app.models.access_control import Permission, Role, RolePermission
from app.models.organization import Organization
from app.models.user import OrganizationMembership, User
from app.modules.projects.service import has_organization_permission


def require_active_membership(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
) -> OrganizationMembership:
    membership = db.scalar(
        select(OrganizationMembership)
        .join(
            Organization,
            Organization.id == OrganizationMembership.organization_id,
        )
        .join(User, User.id == OrganizationMembership.user_id)
        .where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.status == "active",
            User.is_active.is_(True),
            Organization.is_active.is_(True),
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization membership not found",
        )
    return membership


def require_access_management(
    db: Session,
    organization_id: uuid.UUID,
    current_user: User,
) -> Organization:
    organization = db.scalar(
        select(Organization).where(
            Organization.id == organization_id,
            Organization.is_active.is_(True),
        )
    )
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    if current_user.is_superuser:
        return organization

    require_active_membership(db, organization_id, current_user.id)
    if not has_organization_permission(
        db,
        current_user,
        organization_id,
        "access_control.manage",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization access-management permission required",
        )
    return organization


def create_standard_roles(
    db: Session,
    organization_id: uuid.UUID,
) -> list[Role]:
    permissions = {
        permission.code: permission
        for permission in db.scalars(
            select(Permission).where(Permission.code.in_(PERMISSIONS))
        )
    }
    if len(permissions) != len(PERMISSIONS):
        raise RuntimeError("Core permissions are missing; apply database migrations")

    roles: list[Role] = []
    for code, (name, permission_codes) in ROLE_TEMPLATES.items():
        role = db.scalar(
            select(Role).where(
                Role.organization_id == organization_id,
                Role.code == code,
            )
        )
        if role is not None:
            if not role.is_system:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role code '{code}' is already used by a custom role",
                )
            roles.append(role)
            continue

        role = Role(
            organization_id=organization_id,
            code=code,
            name=name,
            description=f"System role: {name}",
            is_system=True,
        )
        db.add(role)
        db.flush()
        db.add_all(
            RolePermission(
                role_id=role.id,
                permission_id=permissions[permission_code].id,
            )
            for permission_code in permission_codes
        )
        roles.append(role)

    return roles
