import uuid
from datetime import time

from pydantic import BaseModel


class TimetableSlotCreate(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    day_of_week: int  # 0 = lundi ... 6 = dimanche
    start_time: time
    end_time: time
    room: str | None = None


class TimetableSlotOut(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    day_of_week: int
    start_time: time
    end_time: time
    room: str | None

    class Config:
        from_attributes = True


class TimetableConflict(BaseModel):
    kind: str  # "teacher" | "class" | "room"
    message: str
    slot_a_id: uuid.UUID
    slot_b_id: uuid.UUID
