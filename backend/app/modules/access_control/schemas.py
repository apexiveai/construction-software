import uuid

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_-]*$")
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str] = Field(min_length=1, max_length=100)


class RoleAssignments(BaseModel):
    role_codes: list[str] = Field(max_length=20)


class BootstrapRequest(BaseModel):
    initial_admin_user_id: uuid.UUID


class RoleRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    permissions: list[str]


class PermissionRead(BaseModel):
    code: str
    name: str
    description: str | None
