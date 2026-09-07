"""
Point d'entrée unique important tous les modèles SIGMA, afin que
Base.metadata connaisse toutes les tables (utilisé par init_db.py et Alembic).
"""
from app.models.organization import Organization, School, Campus, AcademicYear, AcademicPeriod
from app.models.user import (
    User, Permission, Post, PostPermission, PermissionScope, UserPost, Delegation, ScopeType,
)
from app.models.audit import AuditLog
from app.models.academic import Level, Stream, ClassGroup, Subject, TeacherAssignment
from app.models.student import Student, Guardian, StudentGuardian, ClassMembership, StudentStatus, MembershipStatus, Gender
from app.models.assessment import Assessment, Grade, GradeStatus
from app.models.finance import FeeStructure, Invoice, Payment, PaymentMethod
from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.discipline import DisciplinaryRecord, DisciplinaryType, DisciplinarySeverity
from app.models.honor_board import HonorBoardRule, HonorBoard, HonorBoardEntry, HonorBoardScopeType
from app.models.timetable import TimetableSlot
from app.models.hr import Contract, ContractType, LeaveRecord, LeaveStatus, PayrollEntry
from app.models.communication import Announcement, AnnouncementChannel, AnnouncementTarget

__all__ = [
    "Organization", "School", "Campus", "AcademicYear", "AcademicPeriod",
    "User", "Permission", "Post", "PostPermission", "PermissionScope", "UserPost", "Delegation", "ScopeType",
    "AuditLog",
    "Level", "Stream", "ClassGroup", "Subject", "TeacherAssignment",
    "Student", "Guardian", "StudentGuardian", "ClassMembership", "StudentStatus", "MembershipStatus", "Gender",
    "Assessment", "Grade", "GradeStatus",
    "FeeStructure", "Invoice", "Payment", "PaymentMethod",
    "AttendanceRecord", "AttendanceStatus",
    "DisciplinaryRecord", "DisciplinaryType", "DisciplinarySeverity",
    "HonorBoardRule", "HonorBoard", "HonorBoardEntry", "HonorBoardScopeType",
    "TimetableSlot",
    "Contract", "ContractType", "LeaveRecord", "LeaveStatus", "PayrollEntry",
    "Announcement", "AnnouncementChannel", "AnnouncementTarget",
]
