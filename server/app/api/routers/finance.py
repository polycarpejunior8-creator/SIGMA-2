"""
Module Finance (cf §28-30, doc2 §12). Règle stricte : aucune suppression physique
d'un paiement. Toute correction passe par ANNULATION + trace d'audit.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.deps import get_current_user, require_permission
from app.database import get_db
from app.models.finance import FeeStructure, Invoice, Payment
from app.models.user import User
from app.schemas.finance import (
    FeeStructureCreate, FeeStructureOut, InvoiceCreate, InvoiceOut,
    PaymentCreate, PaymentUpdate, PaymentCancel, PaymentOut,
)

router = APIRouter(prefix="/api", tags=["Finance"])


# ---------- Tarifs ----------

@router.get("/schools/{school_id}/fee-structures", response_model=list[FeeStructureOut])
def list_fee_structures(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(FeeStructure).where(FeeStructure.school_id == school_id)).scalars().all()


@router.post("/fee-structures", response_model=FeeStructureOut, status_code=201)
def create_fee_structure(
    payload: FeeStructureCreate, db: Session = Depends(get_db),
    _: User = Depends(require_permission("finance.manage_fee_structures")),
):
    fee = FeeStructure(**payload.model_dump())
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return fee


# ---------- Factures ----------

@router.get("/students/{student_id}/invoices", response_model=list[InvoiceOut])
def list_invoices(
    student_id: uuid.UUID, db: Session = Depends(get_db),
    _: User = Depends(require_permission("finance.view_payments")),
):
    return db.execute(select(Invoice).where(Invoice.student_id == student_id)).scalars().all()


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(
    payload: InvoiceCreate, db: Session = Depends(get_db),
    _: User = Depends(require_permission("finance.manage_fee_structures")),
):
    invoice = Invoice(**payload.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


# ---------- Paiements & Reçus ----------

def _generate_receipt_number(db: Session) -> str:
    """Génère un numéro de reçu unique : REC-<année>-<compteur> (cf doc2 §12)."""
    year = datetime.now(timezone.utc).year
    count = db.execute(select(func.count()).select_from(Payment)).scalar_one()
    return f"REC-{year}-{count + 1:06d}"


@router.get("/invoices/{invoice_id}/payments", response_model=list[PaymentOut])
def list_payments(
    invoice_id: uuid.UUID, db: Session = Depends(get_db),
    _: User = Depends(require_permission("finance.view_payments")),
):
    return db.execute(select(Payment).where(Payment.invoice_id == invoice_id)).scalars().all()


@router.post("/payments", response_model=PaymentOut, status_code=201)
def record_payment(
    payload: PaymentCreate, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("finance.record_payment")),
):
    invoice = db.get(Invoice, payload.invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture introuvable.")

    payment = Payment(
        invoice_id=payload.invoice_id,
        received_by_id=current_user.id,
        receipt_number=_generate_receipt_number(db),
        amount=payload.amount,
        method=payload.method,
        paid_at=payload.paid_at or datetime.now(timezone.utc),
    )
    db.add(payment)
    db.flush()

    record_audit(
        db, user=current_user, school_id=invoice.student.school_id, action="payment.create",
        entity_type="Payment", entity_id=str(payment.id),
        new_value={"amount": float(payload.amount), "receipt_number": payment.receipt_number},
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.patch("/payments/{payment_id}", response_model=PaymentOut)
def edit_payment(
    payment_id: uuid.UUID,
    payload: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("finance.edit_payment")),
):
    """
    Toute modification d'un paiement est tracée intégralement (ancienne/nouvelle valeur),
    exactement comme illustré au §14 du cahier des charges.
    """
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")
    if payment.is_cancelled:
        raise HTTPException(status_code=409, detail="Un paiement annulé ne peut plus être modifié.")

    old_value = {"amount": float(payment.amount), "method": payment.method.value}
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(payment, field, value)

    record_audit(
        db, user=current_user, school_id=payment.invoice.student.school_id, action="payment.update",
        entity_type="Payment", entity_id=str(payment.id),
        old_value=old_value, new_value={k: (v.value if hasattr(v, "value") else v) for k, v in changes.items()},
        device_label=None,
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/payments/{payment_id}/cancel", response_model=PaymentOut)
def cancel_payment(
    payment_id: uuid.UUID,
    payload: PaymentCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("finance.cancel_payment")),
):
    """Annulation logique uniquement — jamais de suppression physique (cf doc2 §12)."""
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")

    payment.is_cancelled = True
    payment.cancelled_reason = payload.reason

    record_audit(
        db, user=current_user, school_id=payment.invoice.student.school_id, action="payment.cancel",
        entity_type="Payment", entity_id=str(payment.id), new_value={"reason": payload.reason},
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/payments/{payment_id}/reprint", response_model=PaymentOut)
def reprint_receipt(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("finance.print_receipt")),
):
    """Une réimpression reste identifiable (compteur incrémenté + trace d'audit, cf §29)."""
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")

    payment.reprint_count += 1
    record_audit(
        db, user=current_user, school_id=payment.invoice.student.school_id, action="payment.reprint",
        entity_type="Payment", entity_id=str(payment.id), new_value={"reprint_count": payment.reprint_count},
    )
    db.commit()
    db.refresh(payment)
    return payment
