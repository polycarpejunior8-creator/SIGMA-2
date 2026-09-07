import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { AcademicPeriod, AcademicYear, ClassGroup, ClassMembershipOut, StudentDetail as StudentDetailType } from "../../types";

export default function StudentDetail() {
  const { id } = useParams<{ id: string }>();
  const { user, can } = useAuth();
  const [student, setStudent] = useState<StudentDetailType | null>(null);
  const [history, setHistory] = useState<ClassMembershipOut[]>([]);
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [periods, setPeriods] = useState<AcademicPeriod[]>([]);
  const [selectedPeriodId, setSelectedPeriodId] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enrollClassId, setEnrollClassId] = useState("");

  const load = async () => {
    if (!id) return;
    try {
      const [studentRes, historyRes] = await Promise.all([
        api.get<StudentDetailType>(`/api/students/${id}`),
        api.get<ClassMembershipOut[]>(`/api/students/${id}/history`),
      ]);
      setStudent(studentRes.data);
      setHistory(historyRes.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!user) return;
    (async () => {
      const yearsRes = await api.get<AcademicYear[]>(`/api/schools/${user.school_id}/academic-years`);
      const current = yearsRes.data.find((y) => y.is_current);
      if (current) {
        const classesRes = await api.get<ClassGroup[]>(`/api/academic-years/${current.id}/classes`);
        setClasses(classesRes.data);
        const periodsRes = await api.get<AcademicPeriod[]>(`/api/academic-years/${current.id}/periods`);
        setPeriods(periodsRes.data);
      }
    })();
  }, [user]);

  const enroll = async () => {
    if (!id || !enrollClassId) return;
    try {
      await api.post("/api/students/enroll", {
        student_id: id, class_id: enrollClassId, enrolled_at: new Date().toISOString().slice(0, 10),
      });
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const downloadReportCard = async () => {
    if (!id || !selectedPeriodId) return;
    setDownloading(true);
    try {
      const response = await api.get(`/api/students/${id}/report-card`, {
        params: { academic_period_id: selectedPeriodId },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `bulletin_${student?.matricule ?? id}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setDownloading(false);
    }
  };

  if (error) return <div className="sigma-error">{error}</div>;
  if (!student) return <div className="sigma-empty">Chargement…</div>;

  return (
    <div>
      <Link to="/students" className="sigma-btn sigma-btn--secondary" style={{ marginBottom: 16, display: "inline-block" }}>← Retour à la liste</Link>

      <div className="sigma-card">
        <h3 className="sigma-card__title">{student.first_name} {student.last_name} — {student.matricule}</h3>
        <div className="sigma-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          <div><strong>{student.date_of_birth ?? "—"}</strong><br /><span style={{ color: "var(--sigma-text-muted)" }}>Naissance</span></div>
          <div><strong>{student.place_of_birth ?? "—"}</strong><br /><span style={{ color: "var(--sigma-text-muted)" }}>Lieu de naissance</span></div>
          <div><strong>{student.gender ?? "—"}</strong><br /><span style={{ color: "var(--sigma-text-muted)" }}>Genre</span></div>
          <div><strong>{student.status}</strong><br /><span style={{ color: "var(--sigma-text-muted)" }}>Statut</span></div>
        </div>
      </div>

      <div className="sigma-card">
        <h3 className="sigma-card__title">Famille</h3>
        <table className="sigma-table">
          <thead><tr><th>Nom</th><th>Relation</th><th>Téléphone</th><th>Email</th><th>Autorisé à récupérer</th></tr></thead>
          <tbody>
            {student.guardians.map((g) => (
              <tr key={g.id}>
                <td>{g.first_name} {g.last_name}</td>
                <td>{g.relationship_type}</td>
                <td>{g.phone ?? "—"}</td>
                <td>{g.email ?? "—"}</td>
                <td>{g.can_pickup ? "Oui" : "Non"}</td>
              </tr>
            ))}
            {student.guardians.length === 0 && <tr><td colSpan={5} className="sigma-empty">Aucun responsable renseigné.</td></tr>}
          </tbody>
        </table>
      </div>

      <div className="sigma-card">
        <h3 className="sigma-card__title">Bulletin</h3>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <select className="sigma-select" style={{ maxWidth: 220 }} value={selectedPeriodId} onChange={(e) => setSelectedPeriodId(e.target.value)}>
            <option value="">— choisir une période —</option>
            {periods.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
          </select>
          <button className="sigma-btn sigma-btn--primary" disabled={!selectedPeriodId || downloading} onClick={downloadReportCard}>
            {downloading ? "Génération…" : "Télécharger le bulletin PDF"}
          </button>
        </div>
      </div>

      <div className="sigma-card">
        <h3 className="sigma-card__title">Historique de scolarité</h3>
        <table className="sigma-table">
          <thead><tr><th>Classe</th><th>Statut</th><th>Depuis</th><th>Jusqu'au</th></tr></thead>
          <tbody>
            {history.map((h) => (
              <tr key={h.id}>
                <td>{classes.find((c) => c.id === h.class_id)?.name ?? h.class_id}</td>
                <td>{h.status}</td>
                <td>{h.enrolled_at}</td>
                <td>{h.left_at ?? "—"}</td>
              </tr>
            ))}
            {history.length === 0 && <tr><td colSpan={4} className="sigma-empty">Aucune inscription enregistrée.</td></tr>}
          </tbody>
        </table>

        {can("students.create") && (
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <select className="sigma-select" value={enrollClassId} onChange={(e) => setEnrollClassId(e.target.value)}>
              <option value="">— choisir une classe —</option>
              {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <button className="sigma-btn sigma-btn--primary" onClick={enroll} disabled={!enrollClassId}>Inscrire dans cette classe</button>
          </div>
        )}
      </div>
    </div>
  );
}
