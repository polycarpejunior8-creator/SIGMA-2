import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator

from app.models.honor_board import HonorBoardScopeType


class HonorBoardRuleCreate(BaseModel):
    school_id: uuid.UUID
    name: str
    min_average: float | None = None
    max_unjustified_absences: int | None = None
    disallow_high_severity_sanction: bool = True
    weight_average: float = 100
    weight_discipline: float = 0
    weight_attendance: float = 0
    weight_progression: float = 0
    max_winners: int | None = None

    @model_validator(mode="after")
    def check_weights(self):
        total = self.weight_average + self.weight_discipline + self.weight_attendance + self.weight_progression
        if round(total, 2) != 100:
            raise ValueError(f"La somme des pondérations doit être égale à 100 (actuellement {total}).")
        return self


class HonorBoardRuleOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    min_average: float | None
    max_unjustified_absences: int | None
    disallow_high_severity_sanction: bool
    weight_average: float
    weight_discipline: float
    weight_attendance: float
    weight_progression: float
    max_winners: int | None

    class Config:
        from_attributes = True


class HonorBoardGenerate(BaseModel):
    rule_id: uuid.UUID
    academic_period_id: uuid.UUID
    scope_type: HonorBoardScopeType
    class_id: uuid.UUID | None = None
    level_id: uuid.UUID | None = None


class HonorBoardEntryOut(BaseModel):
    student_id: uuid.UUID
    average: float
    unjustified_absences: int
    discipline_points: float
    score: float
    rank: int

    class Config:
        from_attributes = True


class HonorBoardOut(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    academic_period_id: uuid.UUID
    scope_type: HonorBoardScopeType
    class_id: uuid.UUID | None
    level_id: uuid.UUID | None
    generated_at: datetime
    is_published: bool
    entries: list[HonorBoardEntryOut]

    class Config:
        from_attributes = True
