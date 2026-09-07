"""
Détection de conflits d'emploi du temps (cf §19) :
    "⚠ Conflit : M. X est affecté simultanément à 3e A et 4e B à 10h."

Trois types de conflits sont détectés : un même enseignant, une même classe, ou une même
salle, sur deux créneaux qui se chevauchent le même jour de la semaine.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.timetable import TimetableSlot


def _overlaps(start_a, end_a, start_b, end_b) -> bool:
    return start_a < end_b and start_b < end_a


def find_conflicts(db: Session, candidate: TimetableSlot, exclude_slot_id=None) -> list[dict]:
    """
    Retourne la liste des conflits détectés pour `candidate` par rapport aux créneaux
    déjà existants le même jour de la semaine.
    """
    stmt = select(TimetableSlot).where(TimetableSlot.day_of_week == candidate.day_of_week)
    if exclude_slot_id is not None:
        stmt = stmt.where(TimetableSlot.id != exclude_slot_id)

    existing_slots = db.execute(stmt).scalars().all()
    conflicts = []

    for other in existing_slots:
        if not _overlaps(candidate.start_time, candidate.end_time, other.start_time, other.end_time):
            continue

        if other.teacher_id == candidate.teacher_id:
            conflicts.append({
                "kind": "teacher",
                "message": "L'enseignant est déjà affecté à un autre cours sur ce créneau.",
                "other_slot_id": other.id,
            })
        if other.class_id == candidate.class_id:
            conflicts.append({
                "kind": "class",
                "message": "Cette classe a déjà un cours programmé sur ce créneau.",
                "other_slot_id": other.id,
            })
        if candidate.room and other.room and other.room == candidate.room:
            conflicts.append({
                "kind": "room",
                "message": f"La salle '{candidate.room}' est déjà occupée sur ce créneau.",
                "other_slot_id": other.id,
            })

    return conflicts
