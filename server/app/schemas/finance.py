import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.finance import PaymentMethod


class FeeStructureCreate(BaseModel):
    school_id: uuid.UUID
    academic_year_id: uuid.UUID
    level_id: uuid.UUID | None = None
    name: str
    category: str
    amount: float


class FeeStructureOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    academic_year_id: uuid.UUID
    level_id: uuid.UUID | None
    name: str
    category: str
    amount: float

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    student_id: uuid.UUID
    fee_structure_id: uuid.UUID
    amount_due: float
    due_date: date | None = None
    discount_amount: float = 0
    is_exempted: bool = False


class InvoiceOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    fee_structure_id: uuid.UUID
    amount_due: float
    due_date: date | None
    discount_amount: float
    is_exempted: bool

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    invoice_id: uuid.UUID
    amount: float
    method: PaymentMethod = PaymentMethod.CASH
    paid_at: datetime | None = None


class PaymentUpdate(BaseModel):
    """Seuls certains champs sont modifiables ; toute modification est auditée (cf §14, §29)."""
    amount: float | None = None
    method: PaymentMethod | None = None


class PaymentCancel(BaseModel):
    reason: str


class PaymentOut(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    receipt_number: str
    amount: float
    method: PaymentMethod
    paid_at: datetime
    is_cancelled: bool
    reprint_count: int

    class Config:
        from_attributes = True
