import uuid

from pydantic import BaseModel

from app.models.assessment import GradeStatus


class AssessmentCreate(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    academic_period_id: uuid.UUID
    title: str
    assessment_type: str
    max_score: float = 20
    coefficient: float = 1


class AssessmentOut(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    academic_period_id: uuid.UUID
    title: str
    assessment_type: str
    max_score: float
    coefficient: float

    class Config:
        from_attributes = True


class GradeIn(BaseModel):
    student_id: uuid.UUID
    score: float | None = None
    is_absent: bool = False


class GradeBulkUpsert(BaseModel):
    """Saisie groupée des notes d'une évaluation (cf §21 - saisie depuis PC/tablette/import)."""
    grades: list[GradeIn]


class GradeOut(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    student_id: uuid.UUID
    score: float | None
    is_absent: bool
    status: GradeStatus

    class Config:
        from_attributes = True


class GradeStatusTransition(BaseModel):
    new_status: GradeStatus
