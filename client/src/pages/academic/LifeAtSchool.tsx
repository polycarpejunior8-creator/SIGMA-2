import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type {
  AcademicYear, AttendanceRecord, AttendanceStatusType, ClassGroup,
  DisciplinaryRecord, DisciplinaryType, DisciplinarySeverity, Student,
} from "../../types";

const ATTENDANCE_LABELS: Record<AttendanceStatusType, string> = {
  present: "Présent", absent: "Absent", late: "Retard",
  excused_absence: "Absence justifiée", authorized_exit: "Sortie autorisée",
};

const DISCIPLINE_TYPE_LABELS: Record<DisciplinaryType, string> = {
  observation: "Observation", warning: "Avertissement", detention: "Retenue",
  sanction: "Sanction", exclusion: "Exclusion", reward: "Récompense",
};

export default function LifeAtSchool() {
  const { user, can } = useAuth();
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [selectedClass, setSelectedClass] = useState("");
  const [students, setStudents] = useState<Student[]>([]);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().slice(0, 10));
  const [error, setError] = useState<string | null>(null);

  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [discipline, setDiscipline] = useState<DisciplinaryRecord[]>([]);
  const [disciplineForm, setDisciplineForm] = useState({
    record_type: "observation" as DisciplinaryType, severity: "low" as DisciplinarySeverity, description: "", points: 0,
  });

  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const yearsRes = await api.get<AcademicYear[]>(`/api/schools/${user.school_id}/academic-years`);
        const current = yearsRes.data.find((y) => y.is_current);
        if (current) {
          const classesRes = await api.get<ClassGroup[]>(`/api/academic-years/${current.id}/classes`);
          setClasses(classesRes.data);
        }
      } catch (err) { setError(apiErrorMessage(err)); }
    })();
  }, [user]);

  useEffect(() => {
    if (!selectedClass) return;
    api.get<Student[]>(`/api/students/by-class/${selectedClass}`).then((r) => setStudents(r.data)).catch((err) => setError(apiErrorMessage(err)));
  }, [selectedClass]);

  useEffect(() => {
    if (!selectedClass || !selectedDate) return;
    api.get<AttendanceRecord[]>(`/api/classes/${selectedClass}/attendance`, { params: { record_date: selectedDate } })
      .then((r) => setAttendance(r.data)).catch((err) => setError(apiErrorMessage(err)));
  }, [selectedClass, selectedDate]);

  useEffect(() => {
    if (!selectedStudentId) return;
    api.get<DisciplinaryRecord[]>(`/api/students/${selectedStudentId}/discipline`).then((r) => setDiscipline(r.data)).catch((err) => setError(apiErrorMessage(err)));
  }, [selectedStudentId]);

  const markAttendance = async (studentId: string, status: AttendanceStatusType) => {
    try {
      await api.post("/api/attendance", { student_id: studentId, class_id: selectedClass, record_date: selectedDate, status });
      const r = await api.get<AttendanceRecord[]>(`/api/classes/${selectedClass}/attendance`, { params: { record_date: selectedDate } });
      setAttendance(r.data);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const justify = async (recordId: string) => {
    const motif = prompt("Motif de la justification :");
    if (!motif) return;
    try {
      await api.post(`/api/attendance/${recordId}/justify`, { motif });
      const r = await api.get<AttendanceRecord[]>(`/api/classes/${selectedClass}/attendance`, { params: { record_date: selectedDate } });
      setAttendance(r.data);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const recordForStudent = (studentId: string) => attendance.find((a) => a.student_id === studentId);

  const submitDiscipline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudentId) return;
    try {
      await api.post("/api/discipline", {
        student_id: selectedStudentId, record_date: new Date().toISOString().slice(0, 10), ...disciplineForm,
      });
      const r = await api.get<DisciplinaryRecord[]>(`/api/students/${selectedStudentId}/discipline`);
      setDiscipline(r.data);
      setDisciplineForm({ record_type: "observation", severity: "low", description: "", points: 0 });
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-card">
        <h3 className="sigma-card__title">Feuille de présence</h3>
        <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <div className="sigma-field">
            <label>Classe</label>
            <select className="sigma-select" value={selectedClass} onChange={(e) => setSelectedClass(e.target.value)}>
              <option value="">— choisir —</option>
              {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="sigma-field">
            <label>Date</label>
            <input className="sigma-input" type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
          </div>
        </div>

        {selectedClass && (
          <table className="sigma-table">
            <thead><tr><th>Élève</th><th>Statut</th><th>Actions</th></tr></thead>
            <tbody>
              {students.map((s) => {
                const record = recordForStudent(s.id);
                return (
                  <tr key={s.id}>
                    <td>{s.first_name} {s.last_name}</td>
                    <td>
                      {record ? (
                        <span className={"sigma-badge " + (record.status === "present" ? "sigma-badge--green" : record.is_justified ? "sigma-badge--blue" : "sigma-badge--red")}>
                          {ATTENDANCE_LABELS[record.status]} {record.is_justified && "(justifiée)"}
                        </span>
                      ) : <span className="sigma-badge sigma-badge--gray">Non renseigné</span>}
                    </td>
                    <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {can("attendance.record") && (
                        <>
                          <button className="sigma-btn sigma-btn--secondary" onClick={() => markAttendance(s.id, "present")}>Présent</button>
                          <button className="sigma-btn sigma-btn--secondary" onClick={() => markAttendance(s.id, "absent")}>Absent</button>
                          <button className="sigma-btn sigma-btn--secondary" onClick={() => markAttendance(s.id, "late")}>Retard</button>
                        </>
                      )}
                      {can("attendance.justify") && record && record.status === "absent" && !record.is_justified && (
                        <button className="sigma-btn sigma-btn--secondary" onClick={() => justify(record.id)}>Justifier</button>
                      )}
                    </td>
                  </tr>
                );
              })}
              {students.length === 0 && <tr><td colSpan={3} className="sigma-empty">Sélectionnez une classe.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      {can("discipline.view") && (
        <div className="sigma-card">
          <h3 className="sigma-card__title">Discipline</h3>
          <div className="sigma-field">
            <label>Élève</label>
            <select className="sigma-select" value={selectedStudentId} onChange={(e) => setSelectedStudentId(e.target.value)}>
              <option value="">— choisir un élève (dans la classe sélectionnée ci-dessus) —</option>
              {students.map((s) => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}
            </select>
          </div>

          {selectedStudentId && (
            <>
              <table className="sigma-table">
                <thead><tr><th>Date</th><th>Type</th><th>Sévérité</th><th>Description</th><th>Points</th></tr></thead>
                <tbody>
                  {discipline.map((d) => (
                    <tr key={d.id}>
                      <td>{d.record_date}</td>
                      <td>{DISCIPLINE_TYPE_LABELS[d.record_type]}</td>
                      <td>
                        <span className={"sigma-badge " + (d.severity === "high" ? "sigma-badge--red" : d.severity === "medium" ? "sigma-badge--orange" : "sigma-badge--gray")}>
                          {d.severity}
                        </span>
                      </td>
                      <td>{d.description}</td>
                      <td>{d.points}</td>
                    </tr>
                  ))}
                  {discipline.length === 0 && <tr><td colSpan={5} className="sigma-empty">Aucun enregistrement.</td></tr>}
                </tbody>
              </table>

              {can("discipline.record") && (
                <form onSubmit={submitDiscipline} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
                  <select className="sigma-select" value={disciplineForm.record_type} onChange={(e) => setDisciplineForm({ ...disciplineForm, record_type: e.target.value as DisciplinaryType })}>
                    {Object.entries(DISCIPLINE_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                  <select className="sigma-select" value={disciplineForm.severity} onChange={(e) => setDisciplineForm({ ...disciplineForm, severity: e.target.value as DisciplinarySeverity })}>
                    <option value="low">Sévérité faible</option>
                    <option value="medium">Sévérité moyenne</option>
                    <option value="high">Sévérité grave</option>
                  </select>
                  <input className="sigma-input" style={{ flex: 1, minWidth: 220 }} placeholder="Description" required value={disciplineForm.description} onChange={(e) => setDisciplineForm({ ...disciplineForm, description: e.target.value })} />
                  <input className="sigma-input" style={{ width: 100 }} type="number" placeholder="Points" value={disciplineForm.points} onChange={(e) => setDisciplineForm({ ...disciplineForm, points: Number(e.target.value) })} />
                  <button className="sigma-btn sigma-btn--primary" type="submit">Enregistrer</button>
                </form>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
