"""
Module Communication (cf §33). Pour ce MVP, seules les annonces internes (affichées dans
l'application) sont réellement envoyées. Les canaux SMS/Email/Push nécessitent la
configuration d'un fournisseur externe (Twilio, SMTP, etc.) : le champ `channel` et le
statut `is_sent` sont prévus pour brancher cette intégration plus tard, sans changer le
modèle de données (cf §33 - Modèles de messages).
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, Text, Enum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class AnnouncementChannel(str, enum.Enum):
    IN_APP = "in_app"
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


class AnnouncementTarget(str, enum.Enum):
    ALL = "all"                      # tout l'établissement
    CLASS = "class"                  # une classe précise
    LEVEL = "level"                  # un niveau précis
    GUARDIANS_UNPAID = "guardians_unpaid"  # parents dont les frais sont impayés (cf §33 exemple)
    STAFF = "staff"                  # personnel uniquement


class Announcement(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "announcements"

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    sent_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[AnnouncementChannel] = mapped_column(Enum(AnnouncementChannel), default=AnnouncementChannel.IN_APP)
    target: Mapped[AnnouncementTarget] = mapped_column(Enum(AnnouncementTarget), default=AnnouncementTarget.ALL)
    target_class_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), nullable=True)
    target_level_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("levels.id", ondelete="CASCADE"), nullable=True)

    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=True)  # False si canal externe pas encore branché
