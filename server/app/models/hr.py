"""
Module RH & Paie (cf §31-32). Le personnel est représenté par le modèle User existant
(un enseignant, un comptable, etc. sont tous des User avec un ou plusieurs Postes) ;
ce module ajoute les informations contractuelles et salariales qui leur sont propres.
"""
import enum
import uuid
from datetime import date

from sqlalchemy import String, ForeignKey, Numeric, Date, Enum, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class ContractType(str, enum.Enum):
    CDI = "cdi"
    CDD = "cdd"
    VACATION = "vacation"     # vacataire
    INTERNSHIP = "internship"


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Contract(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "contracts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))

    contract_type: Mapped[ContractType] = mapped_column(Enum(ContractType), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    base_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["object"] = relationship("User")


class LeaveRecord(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "leave_records"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    leave_type: Mapped[str] = mapped_column(String(100), nullable=False)  # congé annuel, maladie, maternité...
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LeaveStatus] = mapped_column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    user: Mapped["object"] = relationship("User", foreign_keys=[user_id])


class PayrollEntry(Base, UUIDPKMixin, TimestampMixin):
    """Une fiche de paie mensuelle (cf §32 : salaire de base + primes + indemnités - retenues)."""
    __tablename__ = "payroll_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    period_label: Mapped[str] = mapped_column(String(20), nullable=False)  # ex: "2026-09"

    base_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    bonuses: Mapped[float] = mapped_column(Numeric(12, 2), default=0)      # primes
    allowances: Mapped[float] = mapped_column(Numeric(12, 2), default=0)  # indemnités
    deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0)  # retenues

    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["object"] = relationship("User")

    @property
    def net_pay(self) -> float:
        return float(self.base_salary) + float(self.bonuses) + float(self.allowances) - float(self.deductions)
