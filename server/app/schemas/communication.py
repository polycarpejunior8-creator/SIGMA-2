import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.communication import AnnouncementChannel, AnnouncementTarget


class AnnouncementCreate(BaseModel):
    school_id: uuid.UUID
    title: str
    body: str
    channel: AnnouncementChannel = AnnouncementChannel.IN_APP
    target: AnnouncementTarget = AnnouncementTarget.ALL
    target_class_id: uuid.UUID | None = None
    target_level_id: uuid.UUID | None = None


class AnnouncementOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    sent_by_id: uuid.UUID
    title: str
    body: str
    channel: AnnouncementChannel
    target: AnnouncementTarget
    target_class_id: uuid.UUID | None
    target_level_id: uuid.UUID | None
    sent_at: datetime
    is_sent: bool

    class Config:
        from_attributes = True
