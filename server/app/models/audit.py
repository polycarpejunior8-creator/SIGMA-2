"""
Journal d'audit (cf §14). Non modifiable par les utilisateurs ordinaires :
aucune route API n'expose de UPDATE/DELETE sur cette table.
"""
import uuid

from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin
from app.models.user import User


class AuditLog(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    school_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_label: Mapped[str | None] = mapped_column(String(255), nullable=True)  # snapshot du nom au moment de l'action

    action: Mapped[str] = mapped_column(String(150), nullable=False)   # ex: "payment.update"
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # ex: "Payment"
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_label: Mapped[str | None] = mapped_column(String(150), nullable=True)  # "PC-COMPTA-02"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(viewonly=True)
