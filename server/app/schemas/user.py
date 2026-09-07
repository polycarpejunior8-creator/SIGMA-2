import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import ScopeType


class UserCreate(BaseModel):
    school_id: uuid.UUID
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    post_ids: list[uuid.UUID] = []


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    photo_url: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    is_active: bool
    is_superadmin: bool
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class PermissionOut(BaseModel):
    id: uuid.UUID
    code: str
    module: str
    label_fr: str
    label_en: str

    class Config:
        from_attributes = True


class PermissionScopeIn(BaseModel):
    scope_type: ScopeType
    scope_id: uuid.UUID | None = None


class PostPermissionAssign(BaseModel):
    """Une ligne de la matrice de permissions attribuée à un poste."""
    permission_code: str
    scopes: list[PermissionScopeIn] = []  # vide => portée établissement entière


class PostCreate(BaseModel):
    school_id: uuid.UUID
    name: str
    description: str | None = None
    permissions: list[PostPermissionAssign] = []


class PostUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[PostPermissionAssign] | None = None  # remplace entièrement la matrice si fourni


class PermissionScopeOut(BaseModel):
    scope_type: ScopeType
    scope_id: uuid.UUID | None

    class Config:
        from_attributes = True


class PostPermissionOut(BaseModel):
    permission: PermissionOut
    scopes: list[PermissionScopeOut]

    class Config:
        from_attributes = True


class PostOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    description: str | None
    is_system: bool
    post_permissions: list[PostPermissionOut]

    class Config:
        from_attributes = True


class UserPostAssign(BaseModel):
    user_id: uuid.UUID
    post_id: uuid.UUID


class DelegationCreate(BaseModel):
    school_id: uuid.UUID
    granted_to_id: uuid.UUID
    permission_code: str
    scope_type: ScopeType = ScopeType.SCHOOL
    scope_id: uuid.UUID | None = None
    reason: str | None = None
    start_at: datetime
    end_at: datetime


class DelegationOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    granted_by_id: uuid.UUID
    granted_to_id: uuid.UUID
    permission_code: str
    scope_type: ScopeType
    scope_id: uuid.UUID | None
    reason: str | None
    start_at: datetime
    end_at: datetime
    is_revoked: bool

    class Config:
        from_attributes = True
