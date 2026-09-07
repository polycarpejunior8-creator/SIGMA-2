import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { AcademicPeriod, AcademicYear, Assessment, ClassGroup, Grade, Student, Subject } from "../../types";

const STATUS_LABELS: Record<Grade["status"], string> = {
  draft: "Brouillon", submitted: "Soumis", checked: "Contrôlé",
  validated: "Validé", locked: "Verrouillé", published: "Publié",
};

const NEXT_STATUS: Record<Grade["status"], Grade["status"] | null> = {
  draft: "submitted", submitted: "checked", checked: "validated",
  validated: "locked", locked: "published", published: null,
};

export default function Grades() {
  const { user } = useAuth();
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [periods, setPeriods] = useState<AcademicPeriod[]>([]);
  const [selectedClass, setSelectedClass] = useState("");
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedPeriod, setSelectedPeriod] = useState("");

  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<Assessment | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [grades, setGrades] = useState<Record<string, Grade>>({});
  const [scores, setScores] = useState<Record<string, string>>({});

  const [newAssessment, setNewAssessment] = useState({ title: "", assessment_type: "devoir", max_score: 20, coefficient: 1 });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const yearsRes = await api.get<AcademicYear[]>(`/api/schools/${user.school_id}/academic-years`);
        const current = yearsRes.data.find((y) => y.is_current);
        if (!current) return;
        const [classesRes, subjectsRes, periodsRes] = await Promise.all([
          api.get<ClassGroup[]>(`/api/academic-years/${current.id}/classes`),
          api.get<Subject[]>(`/api/schools/${user.school_id}/subjects`),
          api.get<AcademicPeriod[]>(`/api/academic-years/${current.id}/periods`),
        ]);
        setClasses(classesRes.data);
        setSubjects(subjectsRes.data);
        setPeriods(periodsRes.data);
      } catch (err) { setError(apiErrorMessage(err)); }
    })();
  }, [user]);

  useEffect(() => {
    if (!selectedClass) { setAssessments([]); return; }
    api.get<Assessment[]>(`/api/classes/${selectedClass}/assessments`)
      .then((res) => setAssessments(res.data.filter((a) => a.subject_id === selectedSubject && a.academic_period_id === selectedPeriod)))
      .catch((err) => setError(apiErrorMessage(err)));
    api.get<Student[]>(`/api/students/by-class/${selectedClass}`)
      .then((res) => setStudents(res.data))
      .catch((err) => setError(apiErrorMessage(err)));
  }, [selectedClass, selectedSubject, selectedPeriod]);

  const createAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClass || !selectedSubject || !selectedPeriod) {
      setError("Sélectionnez une classe, une matière et une période.");
      return;
    }
    try {
      const { data } = await api.post<Assessment>("/api/assessments", {
        class_id: selectedClass, subject_id: selectedSubject, academic_period_id: selectedPeriod, ...newAssessment,
      });
      setAssessments((a) => [...a, data]);
      setNewAssessment({ title: "", assessment_type: "devoir", max_score: 20, coefficient: 1 });
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const openAssessment = (a: Assessment) => {
    setSelectedAssessment(a);
    setGrades({});
    setScores({});
  };

  const saveGrades = async () => {
    if (!selectedAssessment) return;
    try {
      const payload = students.map((s) => ({
        student_id: s.id,
        score: scores[s.id] === undefined || scores[s.id] === "" ? null : Number(scores[s.id]),
        is_absent: scores[s.id] === "ABS",
      }));
      const { data } = await api.put<Grade[]>(`/api/assessments/${selectedAssessment.id}/grades`, { grades: payload });
      const map: Record<string, Grade> = {};
      data.forEach((g) => (map[g.student_id] = g));
      setGrades(map);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const transition = async (grade: Grade) => {
    const next = NEXT_STATUS[grade.status];
    if (!next) return;
    try {
      const { data } = await api.post<Grade>(`/api/grades/${grade.id}/transition`, { new_status: next });
      setGrades((g) => ({ ...g, [data.student_id]: data }));
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const transitionAll = async () => {
    const gradeList: Grade[] = Object.values(grades);
    if (gradeList.length === 0) return;
    const next = NEXT_STATUS[gradeList[0].status];
    if (!next) return;
    for (const g of gradeList) {
      if (NEXT_STATUS[g.status] === next) {
        await transition(g);
      }
    }
  };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-card">
        <h3 className="sigma-card__title">Sélection</h3>
        <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
          <div className="sigma-field">
            <label>Classe</label>
            <select className="sigma-select" value={selectedClass} onChange={(e) => setSelectedClass(e.target.value)}>
              <option value="">— choisir —</option>
              {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="sigma-field">
            <label>Matière</label>
            <select className="sigma-select" value={selectedSubject} onChange={(e) => setSelectedSubject(e.target.value)}>
              <option value="">— choisir —</option>
              {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div className="sigma-field">
            <label>Période</label>
            <select className="sigma-select" value={selectedPeriod} onChange={(e) => setSelectedPeriod(e.target.value)}>
              <option value="">— choisir —</option>
              {periods.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
          </div>
        </div>
      </div>

      {selectedClass && selectedSubject && selectedPeriod && (
        <div className="sigma-card">
          <h3 className="sigma-card__title">Évaluations</h3>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
            {assessments.map((a) => (
              <button
                key={a.id}
                className={"sigma-btn " + (selectedAssessment?.id === a.id ? "sigma-btn--primary" : "sigma-btn--secondary")}
                onClick={() => openAssessment(a)}
              >
                {a.title}
              </button>
            ))}
            {assessments.length === 0 && <span className="sigma-empty">Aucune évaluation pour cette sélection.</span>}
          </div>
          <form onSubmit={createAssessment} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <input className="sigma-input" style={{ width: 200 }} placeholder="Titre (ex: Devoir 1)" required value={newAssessment.title} onChange={(e) => setNewAssessment({ ...newAssessment, title: e.target.value })} />
            <select className="sigma-select" style={{ width: 160 }} value={newAssessment.assessment_type} onChange={(e) => setNewAssessment({ ...newAssessment, assessment_type: e.target.value })}>
              <option value="devoir">Devoir</option>
              <option value="interrogation">Interrogation</option>
              <option value="composition">Composition</option>
              <option value="examen">Examen</option>
            </select>
            <input className="sigma-input" style={{ width: 100 }} type="number" placeholder="Barème" value={newAssessment.max_score} onChange={(e) => setNewAssessment({ ...newAssessment, max_score: Number(e.target.value) })} />
            <input className="sigma-input" style={{ width: 100 }} type="number" step="0.5" placeholder="Coefficient" value={newAssessment.coefficient} onChange={(e) => setNewAssessment({ ...newAssessment, coefficient: Number(e.target.value) })} />
            <button className="sigma-btn sigma-btn--primary" type="submit">+ Nouvelle évaluation</button>
          </form>
        </div>
      )}

      {selectedAssessment && (
        <div className="sigma-card">
          <div className="sigma-toolbar">
            <h3 className="sigma-card__title" style={{ margin: 0 }}>Saisie — {selectedAssessment.title}</h3>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="sigma-btn sigma-btn--secondary" onClick={saveGrades}>Enregistrer les notes</button>
              <button className="sigma-btn sigma-btn--primary" onClick={transitionAll} disabled={Object.keys(grades).length === 0}>
                Faire avancer le statut
              </button>
            </div>
          </div>
          <table className="sigma-table">
            <thead>
              <tr><th>Élève</th><th>Note (/{selectedAssessment.max_score})</th><th>Statut</th></tr>
            </thead>
            <tbody>
              {students.map((s) => {
                const grade = grades[s.id];
                return (
                  <tr key={s.id}>
                    <td>{s.first_name} {s.last_name} ({s.matricule})</td>
                    <td>
                      <input
                        className="sigma-input"
                        style={{ width: 100 }}
                        placeholder="Note ou ABS"
                        disabled={grade?.status === "locked" || grade?.status === "published"}
                        value={scores[s.id] ?? (grade?.is_absent ? "ABS" : grade?.score ?? "")}
                        onChange={(e) => setScores((sc) => ({ ...sc, [s.id]: e.target.value }))}
                      />
                    </td>
                    <td>
                      {grade ? (
                        <span className="sigma-badge sigma-badge--blue">{STATUS_LABELS[grade.status]}</span>
                      ) : (
                        <span className="sigma-badge sigma-badge--gray">Non saisie</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {students.length === 0 && <tr><td colSpan={3} className="sigma-empty">Aucun élève inscrit dans cette classe.</td></tr>}
            </tbody>
          </table>
          <p style={{ fontSize: 12, color: "var(--sigma-text-muted)" }}>
            Cycle de vie : Brouillon → Soumis → Contrôlé → Validé → Verrouillé → Publié.
            Utilisez "Faire avancer le statut" pour transitionner l'ensemble du groupe étape par étape.
          </p>
        </div>
      )}
    </div>
  );
}
