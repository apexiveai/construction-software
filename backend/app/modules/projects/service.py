import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_control import MembershipRole, Permission, Role, RolePermission
from app.models.organization import Organization
from app.models.user import OrganizationMembership, User
from app.modules.projects.models import Project


def active_organization_ids(db: Session, user: User) -> list[uuid.UUID]:
    if user.is_superuser:
        return list(
            db.scalars(
                select(Organization.id).where(Organization.is_active.is_(True))
            )
        )

    return list(
        db.scalars(
            select(OrganizationMembership.organization_id)
            .join(
                Organization,
                Organization.id == OrganizationMembership.organization_id,
            )
            .where(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.status == "active",
                Organization.is_active.is_(True),
            )
        )
    )


def has_organization_permission(
    db: Session,
    user: User,
    organization_id: uuid.UUID,
    permission_code: str,
) -> bool:
    if user.is_superuser:
        return bool(
            db.scalar(
                select(Organization.id).where(
                    Organization.id == organization_id,
                    Organization.is_active.is_(True),
                )
            )
        )

    return bool(
        db.scalar(
            select(OrganizationMembership.id)
            .join(
                MembershipRole,
                MembershipRole.membership_id == OrganizationMembership.id,
            )
            .join(Role, Role.id == MembershipRole.role_id)
            .join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .join(
                Organization,
                Organization.id == OrganizationMembership.organization_id,
            )
            .where(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.status == "active",
                Organization.is_active.is_(True),
                Permission.code == permission_code,
                (Role.organization_id == organization_id)
                | (Role.organization_id.is_(None)),
            )
            .limit(1)
        )
    )


def permitted_organization_ids(
    db: Session,
    user: User,
    permission_code: str,
) -> list[uuid.UUID]:
    if user.is_superuser:
        return active_organization_ids(db, user)

    return list(
        db.scalars(
            select(OrganizationMembership.organization_id)
            .join(
                MembershipRole,
                MembershipRole.membership_id == OrganizationMembership.id,
            )
            .join(Role, Role.id == MembershipRole.role_id)
            .join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .join(
                Organization,
                Organization.id == OrganizationMembership.organization_id,
            )
            .where(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.status == "active",
                Organization.is_active.is_(True),
                Permission.code == permission_code,
                (Role.organization_id == OrganizationMembership.organization_id)
                | (Role.organization_id.is_(None)),
            )
            .distinct()
        )
    )


def get_accessible_project(
    db: Session,
    project_id: uuid.UUID,
    organization_ids: list[uuid.UUID],
) -> Project | None:
    if not organization_ids:
        return None

    return db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id.in_(organization_ids),
        )
    )
