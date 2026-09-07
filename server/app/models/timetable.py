"""
Emploi du temps (cf §19). Le modèle reste volontairement simple pour le MVP :
un créneau récurrent hebdomadaire par classe/matière/enseignant/salle.
La détection de conflits (cf §19 exemple) est implémentée dans
`app/core/timetable_engine.py`, appelée à chaque création/modification de créneau.
"""
import uuid
from datetime import time

from sqlalchemy import ForeignKey, Integer, Time, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class TimetableSlot(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "timetable_slots"

    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 = lundi ... 6 = dimanche
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str | None] = mapped_column(String(100), nullable=True)

    class_group: Mapped["object"] = relationship("ClassGroup")
    subject: Mapped["object"] = relationship("Subject")
    teacher: Mapped["object"] = relationship("User")
