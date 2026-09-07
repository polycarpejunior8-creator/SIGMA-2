import uuid
from datetime import date

from pydantic import BaseModel

from app.models.student import Gender, StudentStatus, MembershipStatus


class GuardianCreate(BaseModel):
    school_id: uuid.UUID
    first_name: str
    last_name: str
    phone: str | None = None
    email: str | None = None
    profession: str | None = None
    address: str | None = None
    relationship_type: str  # utilisé uniquement lors de la création liée à un élève
    is_primary_contact: bool = False
    can_pickup: bool = True


class GuardianOut(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    phone: str | None
    email: str | None
    relationship_type: str | None = None
    is_primary_contact: bool | None = None
    can_pickup: bool | None = None

    class Config:
        from_attributes = True


class StudentCreate(BaseModel):
    school_id: uuid.UUID
    matricule: str
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    place_of_birth: str | None = None
    gender: Gender | None = None
    nationality: str | None = None
    address: str | None = None
    guardians: list[GuardianCreate] = []


class StudentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    place_of_birth: str | None = None
    gender: Gender | None = None
    nationality: str | None = None
    address: str | None = None
    status: StudentStatus | None = None
    photo_url: str | None = None


class StudentOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    matricule: str
    first_name: str
    last_name: str
    date_of_birth: date | None
    gender: Gender | None
    status: StudentStatus
    photo_url: str | None

    class Config:
        from_attributes = True


class StudentDetailOut(StudentOut):
    place_of_birth: str | None
    nationality: str | None
    address: str | None
    guardians: list[GuardianOut] = []

    class Config:
        from_attributes = True


class EnrollmentCreate(BaseModel):
    student_id: uuid.UUID
    class_id: uuid.UUID
    enrolled_at: date


class ClassMembershipOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    class_id: uuid.UUID
    status: MembershipStatus
    enrolled_at: date
    left_at: date | None

    class Config:
        from_attributes = True
