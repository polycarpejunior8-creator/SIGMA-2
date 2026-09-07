import uuid

from pydantic import BaseModel


class LevelCreate(BaseModel):
    school_id: uuid.UUID
    name: str
    order_index: int = 0


class LevelOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    order_index: int

    class Config:
        from_attributes = True


class StreamCreate(BaseModel):
    level_id: uuid.UUID
    name: str


class StreamOut(BaseModel):
    id: uuid.UUID
    level_id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


class ClassGroupCreate(BaseModel):
    academic_year_id: uuid.UUID
    level_id: uuid.UUID
    stream_id: uuid.UUID | None = None
    campus_id: uuid.UUID | None = None
    name: str
    homeroom_teacher_id: uuid.UUID | None = None
    capacity: int | None = None


class ClassGroupOut(BaseModel):
    id: uuid.UUID
    academic_year_id: uuid.UUID
    level_id: uuid.UUID
    stream_id: uuid.UUID | None
    name: str
    homeroom_teacher_id: uuid.UUID | None
    capacity: int | None

    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    school_id: uuid.UUID
    code: str
    name: str
    default_coefficient: float = 1


class SubjectOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    code: str
    name: str
    default_coefficient: float

    class Config:
        from_attributes = True


class TeacherAssignmentCreate(BaseModel):
    teacher_id: uuid.UUID
    subject_id: uuid.UUID
    class_id: uuid.UUID
    coefficient_override: float | None = None
    weekly_hours: float | None = None


class TeacherAssignmentOut(BaseModel):
    id: uuid.UUID
    teacher_id: uuid.UUID
    subject_id: uuid.UUID
    class_id: uuid.UUID
    coefficient_override: float | None
    weekly_hours: float | None

    class Config:
        from_attributes = True
