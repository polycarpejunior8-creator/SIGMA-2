"""
Module Communication (cf §33). Cf note dans app/models/communication.py concernant
les canaux externes (SMS/Email/Push) non branchés dans ce MVP.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.database import get_db
from app.models.communication import Announcement, AnnouncementChannel
from app.models.user import User
from app.schemas.communication import AnnouncementCreate, AnnouncementOut

router = APIRouter(prefix="/api/announcements", tags=["Communication"])


@router.get("", response_model=list[AnnouncementOut])
def list_announcements(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("communication.send"))):
    return db.execute(
        select(Announcement).where(Announcement.school_id == school_id).order_by(Announcement.sent_at.desc())
    ).scalars().all()


@router.post("", response_model=AnnouncementOut, status_code=201)
def send_announcement(
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("communication.send")),
):
    # Seul le canal "in_app" est réellement délivré dans ce MVP (cf docstring du modèle).
    is_sent = payload.channel == AnnouncementChannel.IN_APP

    announcement = Announcement(
        **payload.model_dump(), sent_by_id=current_user.id,
        sent_at=datetime.now(timezone.utc), is_sent=is_sent,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement
