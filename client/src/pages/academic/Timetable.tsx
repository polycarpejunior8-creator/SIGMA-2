import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { AcademicYear, ClassGroup, Subject, TimetableSlot, UserOut } from "../../types";

const DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];

export default function Timetable() {
  const { user, can } = useAuth();
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [teachers, setTeachers] = useState<UserOut[]>([]);
  const [selectedClass, setSelectedClass] = useState("");
  const [slots, setSlots] = useState<TimetableSlot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<any[] | null>(null);

  const [form, setForm] = useState({ subject_id: "", teacher_id: "", day_of_week: 0, start_time: "08:00", end_time: "09:00", room: "" });

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
        const subjectsRes = await api.get<Subject[]>(`/api/schools/${user.school_id}/subjects`);
        setSubjects(subjectsRes.data);
        const usersRes = await api.get<UserOut[]>("/api/users", { params: { school_id: user.school_id } });
        setTeachers(usersRes.data);
      } catch (err) { setError(apiErrorMessage(err)); }
    })();
  }, [user]);

  const loadSlots = async () => {
    if (!selectedClass) return;
    try {
      const res = await api.get<TimetableSlot[]>(`/api/classes/${selectedClass}/timetable`);
      setSlots(res.data);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  useEffect(() => {
    loadSlots();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedClass]);

  const submit = async (e: React.FormEvent, force = false) => {
    e.preventDefault();
    if (!selectedClass) return;
    setConflicts(null);
    try {
      await api.post("/api/timetable-slots", { class_id: selectedClass, ...form }, { params: { force } });
      setForm({ subject_id: "", teacher_id: "", day_of_week: 0, start_time: "08:00", end_time: "09:00", room: "" });
      loadSlots();
    } catch (err: any) {
      if (err?.response?.status === 409) {
        setConflicts(err.response.data.detail.conflicts);
      } else {
        setError(apiErrorMessage(err));
      }
    }
  };

  const deleteSlot = async (id: string) => {
    if (!confirm("Supprimer ce créneau ?")) return;
    try {
      await api.delete(`/api/timetable-slots/${id}`);
      loadSlots();
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const subjectName = (id: string) => subjects.find((s) => s.id === id)?.name ?? id;
  const teacherName = (id: string) => { const t = teachers.find((u) => u.id === id); return t ? `${t.first_name} ${t.last_name}` : id; };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-card">
        <div className="sigma-field">
          <label>Classe</label>
          <select className="sigma-select" value={selectedClass} onChange={(e) => setSelectedClass(e.target.value)}>
            <option value="">— choisir —</option>
            {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        {selectedClass && (
          <table className="sigma-table">
            <thead><tr><th>Jour</th><th>Horaire</th><th>Matière</th><th>Enseignant</th><th>Salle</th><th></th></tr></thead>
            <tbody>
              {slots.slice().sort((a, b) => a.day_of_week - b.day_of_week || a.start_time.localeCompare(b.start_time)).map((s) => (
                <tr key={s.id}>
                  <td>{DAYS[s.day_of_week]}</td>
                  <td>{s.start_time} – {s.end_time}</td>
                  <td>{subjectName(s.subject_id)}</td>
                  <td>{teacherName(s.teacher_id)}</td>
                  <td>{s.room ?? "—"}</td>
                  <td>{can("timetable.manage") && <button className="sigma-btn sigma-btn--danger" onClick={() => deleteSlot(s.id)}>Retirer</button>}</td>
                </tr>
              ))}
              {slots.length === 0 && <tr><td colSpan={6} className="sigma-empty">Aucun créneau.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      {selectedClass && can("timetable.manage") && (
        <div className="sigma-card">
          <h3 className="sigma-card__title">Ajouter un créneau</h3>

          {conflicts && (
            <div className="sigma-error">
              ⚠ Conflit(s) détecté(s) :
              <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                {conflicts.map((c, i) => <li key={i}>{c.message}</li>)}
              </ul>
              <button className="sigma-btn sigma-btn--danger" style={{ marginTop: 8 }} onClick={(e) => submit(e, true)}>
                Forcer la création malgré le conflit
              </button>
            </div>
          )}

          <form onSubmit={submit}>
            <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
              <div className="sigma-field">
                <label>Jour</label>
                <select className="sigma-select" value={form.day_of_week} onChange={(e) => setForm({ ...form, day_of_week: Number(e.target.value) })}>
                  {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                </select>
              </div>
              <div className="sigma-field">
                <label>Début</label>
                <input className="sigma-input" type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
              </div>
              <div className="sigma-field">
                <label>Fin</label>
                <input className="sigma-input" type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
              </div>
              <div className="sigma-field">
                <label>Matière</label>
                <select className="sigma-select" required value={form.subject_id} onChange={(e) => setForm({ ...form, subject_id: e.target.value })}>
                  <option value="">— choisir —</option>
                  {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div className="sigma-field">
                <label>Enseignant</label>
                <select className="sigma-select" required value={form.teacher_id} onChange={(e) => setForm({ ...form, teacher_id: e.target.value })}>
                  <option value="">— choisir —</option>
                  {teachers.map((t) => <option key={t.id} value={t.id}>{t.first_name} {t.last_name}</option>)}
                </select>
              </div>
              <div className="sigma-field">
                <label>Salle</label>
                <input className="sigma-input" value={form.room} onChange={(e) => setForm({ ...form, room: e.target.value })} />
              </div>
            </div>
            <button className="sigma-btn sigma-btn--primary" type="submit">Ajouter le créneau</button>
          </form>
        </div>
      )}
    </div>
  );
}
