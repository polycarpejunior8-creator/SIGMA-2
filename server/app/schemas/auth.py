import uuid

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMe(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    school_id: uuid.UUID
    is_superadmin: bool
    permissions: list[str]
    posts: list[str]

    class Config:
        from_attributes = True
