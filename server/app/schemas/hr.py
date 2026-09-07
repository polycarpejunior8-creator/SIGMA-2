import uuid
from datetime import date

from pydantic import BaseModel

from app.models.hr import ContractType, LeaveStatus


class ContractCreate(BaseModel):
    user_id: uuid.UUID
    school_id: uuid.UUID
    contract_type: ContractType
    start_date: date
    end_date: date | None = None
    base_salary: float
    notes: str | None = None


class ContractOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    school_id: uuid.UUID
    contract_type: ContractType
    start_date: date
    end_date: date | None
    base_salary: float
    notes: str | None

    class Config:
        from_attributes = True


class LeaveRecordCreate(BaseModel):
    user_id: uuid.UUID
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveRecordOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None
    status: LeaveStatus
    approved_by_id: uuid.UUID | None

    class Config:
        from_attributes = True


class LeaveDecision(BaseModel):
    approve: bool


class PayrollEntryCreate(BaseModel):
    user_id: uuid.UUID
    period_label: str
    base_salary: float
    bonuses: float = 0
    allowances: float = 0
    deductions: float = 0


class PayrollEntryOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    period_label: str
    base_salary: float
    bonuses: float
    allowances: float
    deductions: float
    is_paid: bool
    net_pay: float

    class Config:
        from_attributes = True
