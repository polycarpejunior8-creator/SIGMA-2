import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.attendance import AttendanceStatus
from app.models.discipline import DisciplinaryType, DisciplinarySeverity


class AttendanceRecordCreate(BaseModel):
    student_id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID | None = None
    record_date: date
    status: AttendanceStatus = AttendanceStatus.ABSENT
    motif: str | None = None


class AttendanceRecordOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID | None
    record_date: date
    status: AttendanceStatus
    motif: str | None
    is_justified: bool
    justified_at: datetime | None

    class Config:
        from_attributes = True


class AttendanceJustify(BaseModel):
    motif: str


class DisciplinaryRecordCreate(BaseModel):
    student_id: uuid.UUID
    record_type: DisciplinaryType
    severity: DisciplinarySeverity = DisciplinarySeverity.LOW
    record_date: date
    description: str
    points: float = 0


class DisciplinaryRecordOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    record_type: DisciplinaryType
    severity: DisciplinarySeverity
    record_date: date
    description: str
    points: float

    class Config:
        from_attributes = True
