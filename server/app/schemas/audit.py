import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID | None
    user_id: uuid.UUID | None
    user_label: str | None
    action: str
    entity_type: str
    entity_id: str | None
    old_value: dict | None
    new_value: dict | None
    ip_address: str | None
    device_label: str | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True
