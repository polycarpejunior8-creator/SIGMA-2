"""
Module Vie scolaire — Présences (cf §26).
Une ligne par élève et par créneau contrôlé (généralement un cours ou une journée).
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import String, ForeignKey, Enum, Boolean, Text, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED_ABSENCE = "excused_absence"   # absence justifiée
    AUTHORIZED_EXIT = "authorized_exit"    # sortie autorisée


class AttendanceRecord(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "attendance_records"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    recorded_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), default=AttendanceStatus.ABSENT)

    motif: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_justified: Mapped[bool] = mapped_column(Boolean, default=False)
    justified_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    justified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["object"] = relationship("Student")
