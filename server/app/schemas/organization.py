import uuid
from datetime import date

from pydantic import BaseModel


class SchoolCreate(BaseModel):
    organization_id: uuid.UUID
    name: str
    code: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    school_type: str | None = None
    regime: str | None = None
    language: str = "fr"
    currency: str = "XAF"
    grading_system: str = "20"


class SchoolOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    code: str
    language: str
    currency: str
    is_active: bool

    class Config:
        from_attributes = True


class CampusCreate(BaseModel):
    school_id: uuid.UUID
    name: str
    address: str | None = None


class CampusOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    is_active: bool

    class Config:
        from_attributes = True


class AcademicYearCreate(BaseModel):
    school_id: uuid.UUID
    label: str
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    label: str
    start_date: date
    end_date: date
    is_current: bool
    is_archived: bool

    class Config:
        from_attributes = True


class AcademicPeriodCreate(BaseModel):
    academic_year_id: uuid.UUID
    label: str
    order_index: int = 1
    start_date: date
    end_date: date


class AcademicPeriodOut(BaseModel):
    id: uuid.UUID
    academic_year_id: uuid.UUID
    label: str
    order_index: int
    start_date: date
    end_date: date
    is_open_for_grading: bool

    class Config:
        from_attributes = True
