"""
Tableaux d'honneur (cf §24) : configuration des règles + génération.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import record_audit
from app.core.deps import get_current_user, require_permission
from app.core.honor_board_engine import compute_honor_board
from app.database import get_db
from app.models.honor_board import HonorBoardRule, HonorBoard, HonorBoardEntry
from app.models.organization import AcademicPeriod
from app.models.user import User
from app.schemas.honor_board import (
    HonorBoardRuleCreate, HonorBoardRuleOut, HonorBoardGenerate, HonorBoardOut,
)

router = APIRouter(prefix="/api", tags=["Tableaux d'honneur"])


@router.get("/schools/{school_id}/honor-board-rules", response_model=list[HonorBoardRuleOut])
def list_rules(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("honor_boards.view"))):
    return db.execute(select(HonorBoardRule).where(HonorBoardRule.school_id == school_id)).scalars().all()


@router.post("/honor-board-rules", response_model=HonorBoardRuleOut, status_code=201)
def create_rule(
    payload: HonorBoardRuleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("honor_boards.manage")),
):
    rule = HonorBoardRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/honor-boards/generate", response_model=HonorBoardOut, status_code=201)
def generate_honor_board(
    payload: HonorBoardGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("honor_boards.manage")),
):
    """SIGMA analyse automatiquement les résultats puis propose le classement (cf §24)."""
    rule = db.get(HonorBoardRule, payload.rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Règle introuvable.")

    period = db.get(AcademicPeriod, payload.academic_period_id)
    if period is None:
        raise HTTPException(status_code=404, detail="Période introuvable.")

    results = compute_honor_board(db, rule, period, payload.scope_type, payload.class_id, payload.level_id)

    board = HonorBoard(
        rule_id=rule.id,
        academic_period_id=period.id,
        scope_type=payload.scope_type,
        class_id=payload.class_id,
        level_id=payload.level_id,
        generated_by_id=current_user.id,
        generated_at=datetime.now(timezone.utc),
    )
    db.add(board)
    db.flush()

    for entry in results:
        db.add(HonorBoardEntry(
            honor_board_id=board.id,
            student_id=entry["student_id"],
            average=entry["average"],
            unjustified_absences=entry["unjustified_absences"],
            discipline_points=entry["discipline_points"],
            score=entry["score"],
            rank=entry["rank"],
        ))

    record_audit(
        db, user=current_user, school_id=None, action="honor_board.generate",
        entity_type="HonorBoard", entity_id=str(board.id), new_value={"eligible_count": len(results)},
    )
    db.commit()

    stmt = select(HonorBoard).options(selectinload(HonorBoard.entries)).where(HonorBoard.id == board.id)
    return db.execute(stmt).scalar_one()


@router.get("/honor-boards/{board_id}", response_model=HonorBoardOut)
def get_honor_board(board_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("honor_boards.view"))):
    stmt = select(HonorBoard).options(selectinload(HonorBoard.entries)).where(HonorBoard.id == board_id)
    board = db.execute(stmt).scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=404, detail="Tableau d'honneur introuvable.")
    return board


@router.post("/honor-boards/{board_id}/publish", response_model=HonorBoardOut)
def publish_honor_board(
    board_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("honor_boards.manage")),
):
    """Le responsable peut valider le tableau avant publication (cf §24)."""
    board = db.get(HonorBoard, board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="Tableau d'honneur introuvable.")
    board.is_published = True
    record_audit(db, user=current_user, school_id=None, action="honor_board.publish", entity_type="HonorBoard", entity_id=str(board.id))
    db.commit()

    stmt = select(HonorBoard).options(selectinload(HonorBoard.entries)).where(HonorBoard.id == board_id)
    return db.execute(stmt).scalar_one()
