"""
Module Finance (cf §28-30, doc2 §12). Un paiement n'est jamais supprimé physiquement :
on utilise ANNULATION + trace d'audit (cf doc2 §12), jamais un DELETE.
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import String, ForeignKey, Numeric, Enum, Date, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    MOBILE_MONEY = "mobile_money"
    OTHER = "other"


class FeeStructure(Base, UUIDPKMixin, TimestampMixin):
    """Un tarif configurable (inscription, scolarité, cantine, transport...)."""
    __tablename__ = "fee_structures"

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    academic_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_years.id", ondelete="CASCADE"))
    level_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("levels.id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)  # ex: "Frais de scolarité 3e"
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # inscription/scolarite/cantine/transport...
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


class Invoice(Base, UUIDPKMixin, TimestampMixin):
    """Une créance d'un élève envers l'établissement pour un tarif donné."""
    __tablename__ = "invoices"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    fee_structure_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fee_structures.id"))
    amount_due: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    is_exempted: Mapped[bool] = mapped_column(Boolean, default=False)

    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")

    student: Mapped["object"] = relationship("Student")
    fee_structure: Mapped["FeeStructure"] = relationship()


class Payment(Base, UUIDPKMixin, TimestampMixin):
    """Un paiement, matérialisé par un reçu numéroté. Annulable, jamais supprimable."""
    __tablename__ = "payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    received_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # ex: REC-2026-000154
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), default=PaymentMethod.CASH)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reprint_count: Mapped[int] = mapped_column(default=0)

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")
    received_by: Mapped["object"] = relationship("User")
