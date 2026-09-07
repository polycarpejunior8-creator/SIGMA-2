"""
Module RH & Paie (cf §31-32).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.deps import get_current_user, require_permission
from app.database import get_db
from app.models.hr import Contract, LeaveRecord, LeaveStatus, PayrollEntry
from app.models.user import User
from app.schemas.hr import (
    ContractCreate, ContractOut, LeaveRecordCreate, LeaveRecordOut, LeaveDecision,
    PayrollEntryCreate, PayrollEntryOut,
)

router = APIRouter(prefix="/api", tags=["RH & Paie"])


# ---------- Contrats ----------

@router.get("/users/{user_id}/contracts", response_model=list[ContractOut])
def list_contracts(user_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("hr.view_staff"))):
    return db.execute(select(Contract).where(Contract.user_id == user_id)).scalars().all()


@router.post("/contracts", response_model=ContractOut, status_code=201)
def create_contract(
    payload: ContractCreate, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hr.manage_contracts")),
):
    contract = Contract(**payload.model_dump())
    db.add(contract)
    db.flush()
    record_audit(
        db, user=current_user, school_id=payload.school_id, action="contract.create",
        entity_type="Contract", entity_id=str(contract.id),
        new_value={"contract_type": payload.contract_type.value, "base_salary": payload.base_salary},
    )
    db.commit()
    db.refresh(contract)
    return contract


# ---------- Congés ----------

@router.get("/users/{user_id}/leave", response_model=list[LeaveRecordOut])
def list_leave(user_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(LeaveRecord).where(LeaveRecord.user_id == user_id)).scalars().all()


@router.post("/leave-requests", response_model=LeaveRecordOut, status_code=201)
def request_leave(
    payload: LeaveRecordCreate, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hr.request_leave")),
):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="La date de fin doit être postérieure à la date de début.")
    leave = LeaveRecord(**payload.model_dump())
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


@router.post("/leave-requests/{leave_id}/decision", response_model=LeaveRecordOut)
def decide_leave(
    leave_id: uuid.UUID,
    payload: LeaveDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hr.approve_leave")),
):
    leave = db.get(LeaveRecord, leave_id)
    if leave is None:
        raise HTTPException(status_code=404, detail="Demande introuvable.")

    leave.status = LeaveStatus.APPROVED if payload.approve else LeaveStatus.REJECTED
    leave.approved_by_id = current_user.id

    record_audit(
        db, user=current_user, school_id=None, action="leave.decision",
        entity_type="LeaveRecord", entity_id=str(leave.id), new_value={"status": leave.status.value},
    )
    db.commit()
    db.refresh(leave)
    return leave


# ---------- Paie ----------

@router.get("/users/{user_id}/payroll", response_model=list[PayrollEntryOut])
def list_payroll(user_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("payroll.view"))):
    entries = db.execute(select(PayrollEntry).where(PayrollEntry.user_id == user_id)).scalars().all()
    return entries


@router.post("/payroll-entries", response_model=PayrollEntryOut, status_code=201)
def create_payroll_entry(
    payload: PayrollEntryCreate, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("payroll.manage")),
):
    """Salaire de base + primes + indemnités - retenues = net à payer (cf §32)."""
    entry = PayrollEntry(**payload.model_dump())
    db.add(entry)
    db.flush()
    record_audit(
        db, user=current_user, school_id=None, action="payroll.create",
        entity_type="PayrollEntry", entity_id=str(entry.id),
        new_value={"period_label": payload.period_label, "net_pay": entry.net_pay},
    )
    db.commit()
    db.refresh(entry)
    return entry
