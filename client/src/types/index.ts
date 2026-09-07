// Types partagés, alignés sur les schémas Pydantic du backend (app/schemas/*.py)

export type ScopeType =
  | "school"
  | "campus"
  | "level"
  | "stream"
  | "class"
  | "subject"
  | "period"
  | "own";

export const SCOPE_TYPE_LABELS: Record<ScopeType, string> = {
  school: "Tout l'établissement",
  campus: "Campus",
  level: "Niveau",
  stream: "Série",
  class: "Classe",
  subject: "Matière",
  period: "Période",
  own: "Ses propres dossiers",
};

export interface UserMe {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  school_id: string;
  is_superadmin: boolean;
  permissions: string[];
  posts: string[];
}

export interface School {
  id: string;
  organization_id: string;
  name: string;
  code: string;
  language: string;
  currency: string;
  is_active: boolean;
}

export interface AcademicYear {
  id: string;
  school_id: string;
  label: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  is_archived: boolean;
}

export interface AcademicPeriod {
  id: string;
  academic_year_id: string;
  label: string;
  order_index: number;
  start_date: string;
  end_date: string;
  is_open_for_grading: boolean;
}

export interface UserOut {
  id: string;
  school_id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  is_active: boolean;
  is_superadmin: boolean;
  last_login_at: string | null;
}

export interface Permission {
  id: string;
  code: string;
  module: string;
  label_fr: string;
  label_en: string;
}

export interface PermissionScope {
  scope_type: ScopeType;
  scope_id: string | null;
}

export interface PostPermission {
  permission: Permission;
  scopes: PermissionScope[];
}

export interface Post {
  id: string;
  school_id: string;
  name: string;
  description: string | null;
  is_system: boolean;
  post_permissions: PostPermission[];
}

export interface Delegation {
  id: string;
  school_id: string;
  granted_by_id: string;
  granted_to_id: string;
  permission_code: string;
  scope_type: ScopeType;
  scope_id: string | null;
  reason: string | null;
  start_at: string;
  end_at: string;
  is_revoked: boolean;
}

export interface AuditLog {
  id: string;
  school_id: string | null;
  user_id: string | null;
  user_label: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  ip_address: string | null;
  device_label: string | null;
  notes: string | null;
  created_at: string;
}

export interface Level {
  id: string;
  school_id: string;
  name: string;
  order_index: number;
}

export interface Stream {
  id: string;
  level_id: string;
  name: string;
}

export interface ClassGroup {
  id: string;
  academic_year_id: string;
  level_id: string;
  stream_id: string | null;
  name: string;
  homeroom_teacher_id: string | null;
  capacity: number | null;
}

export interface Subject {
  id: string;
  school_id: string;
  code: string;
  name: string;
  default_coefficient: number;
}

export interface Student {
  id: string;
  school_id: string;
  matricule: string;
  first_name: string;
  last_name: string;
  date_of_birth: string | null;
  gender: "M" | "F" | null;
  status: string;
  photo_url: string | null;
}

export interface Guardian {
  id: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  email: string | null;
  relationship_type?: string;
  is_primary_contact?: boolean;
  can_pickup?: boolean;
}

export interface StudentDetail extends Student {
  place_of_birth: string | null;
  nationality: string | null;
  address: string | null;
  guardians: Guardian[];
}

export interface ClassMembershipOut {
  id: string;
  student_id: string;
  class_id: string;
  status: string;
  enrolled_at: string;
  left_at: string | null;
}

export interface Assessment {
  id: string;
  class_id: string;
  subject_id: string;
  academic_period_id: string;
  title: string;
  assessment_type: string;
  max_score: number;
  coefficient: number;
}

export interface Grade {
  id: string;
  assessment_id: string;
  student_id: string;
  score: number | null;
  is_absent: boolean;
  status: "draft" | "submitted" | "checked" | "validated" | "locked" | "published";
}

export interface FeeStructure {
  id: string;
  school_id: string;
  academic_year_id: string;
  level_id: string | null;
  name: string;
  category: string;
  amount: number;
}

export interface Invoice {
  id: string;
  student_id: string;
  fee_structure_id: string;
  amount_due: number;
  due_date: string | null;
  discount_amount: number;
  is_exempted: boolean;
}

export interface Payment {
  id: string;
  invoice_id: string;
  receipt_number: string;
  amount: number;
  method: string;
  paid_at: string;
  is_cancelled: boolean;
  reprint_count: number;
}

export interface DashboardData {
  active_students: number;
  classes_count: number;
  average_grade: number | null;
  total_collected: number;
  total_due: number;
  unpaid_amount: number;
}

// ---------- Vie scolaire ----------

export type AttendanceStatusType = "present" | "absent" | "late" | "excused_absence" | "authorized_exit";

export interface AttendanceRecord {
  id: string;
  student_id: string;
  class_id: string;
  subject_id: string | null;
  record_date: string;
  status: AttendanceStatusType;
  motif: string | null;
  is_justified: boolean;
  justified_at: string | null;
}

export type DisciplinaryType = "observation" | "warning" | "detention" | "sanction" | "exclusion" | "reward";
export type DisciplinarySeverity = "low" | "medium" | "high";

export interface DisciplinaryRecord {
  id: string;
  student_id: string;
  record_type: DisciplinaryType;
  severity: DisciplinarySeverity;
  record_date: string;
  description: string;
  points: number;
}

// ---------- Tableaux d'honneur ----------

export type HonorBoardScopeType = "class" | "level" | "school";

export interface HonorBoardRule {
  id: string;
  school_id: string;
  name: string;
  min_average: number | null;
  max_unjustified_absences: number | null;
  disallow_high_severity_sanction: boolean;
  weight_average: number;
  weight_discipline: number;
  weight_attendance: number;
  weight_progression: number;
  max_winners: number | null;
}

export interface HonorBoardEntryOut {
  student_id: string;
  average: number;
  unjustified_absences: number;
  discipline_points: number;
  score: number;
  rank: number;
}

export interface HonorBoardOut {
  id: string;
  rule_id: string;
  academic_period_id: string;
  scope_type: HonorBoardScopeType;
  class_id: string | null;
  level_id: string | null;
  generated_at: string;
  is_published: boolean;
  entries: HonorBoardEntryOut[];
}

// ---------- Emploi du temps ----------

export interface TimetableSlot {
  id: string;
  class_id: string;
  subject_id: string;
  teacher_id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  room: string | null;
}

// ---------- RH & Paie ----------

export type ContractType = "cdi" | "cdd" | "vacation" | "internship";
export type LeaveStatusType = "pending" | "approved" | "rejected";

export interface Contract {
  id: string;
  user_id: string;
  school_id: string;
  contract_type: ContractType;
  start_date: string;
  end_date: string | null;
  base_salary: number;
  notes: string | null;
}

export interface LeaveRecord {
  id: string;
  user_id: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  reason: string | null;
  status: LeaveStatusType;
  approved_by_id: string | null;
}

export interface PayrollEntry {
  id: string;
  user_id: string;
  period_label: string;
  base_salary: number;
  bonuses: number;
  allowances: number;
  deductions: number;
  is_paid: boolean;
  net_pay: number;
}

// ---------- Communication ----------

export type AnnouncementChannel = "in_app" | "sms" | "email" | "push";
export type AnnouncementTarget = "all" | "class" | "level" | "guardians_unpaid" | "staff";

export interface Announcement {
  id: string;
  school_id: string;
  sent_by_id: string;
  title: string;
  body: string;
  channel: AnnouncementChannel;
  target: AnnouncementTarget;
  target_class_id: string | null;
  target_level_id: string | null;
  sent_at: string;
  is_sent: boolean;
}
