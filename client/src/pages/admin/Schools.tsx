import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { AcademicYear, School } from "../../types";

export default function Schools() {
  const { user } = useAuth();
  const [school, setSchool] = useState<School | null>(null);
  const [years, setYears] = useState<AcademicYear[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [label, setLabel] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const load = async () => {
    if (!user) return;
    try {
      const [schoolsRes, yearsRes] = await Promise.all([
        api.get<School[]>("/api/schools"),
        api.get<AcademicYear[]>(`/api/schools/${user.school_id}/academic-years`),
      ]);
      setSchool(schoolsRes.data.find((s) => s.id === user.school_id) ?? null);
      setYears(yearsRes.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const createYear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    try {
      await api.post("/api/academic-years", {
        school_id: user.school_id,
        label,
        start_date: startDate,
        end_date: endDate,
        is_current: false,
      });
      setLabel("");
      setStartDate("");
      setEndDate("");
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const archiveYear = async (id: string) => {
    if (!confirm("Clôturer et archiver cette année scolaire ? Elle deviendra protégée en écriture.")) return;
    try {
      await api.post(`/api/academic-years/${id}/archive`);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-card">
        <h3 className="sigma-card__title">Établissement</h3>
        {school ? (
          <div className="sigma-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
            <div><strong>{school.name}</strong><br /><span style={{ color: "var(--sigma-text-muted)" }}>Nom</span></div>
            <div><strong>{school.code}</strong><br /><span style={{ color: "var(--sigma-text-muted)" }}>Code</span></div>
            <div><strong>{school.language.toUpperCase()}</strong><br /><span style={{ color: "var(--sigma-text-muted)" }}>Langue</span></div>
            <div><strong>{school.currency}</strong><br /><span style={{ color: "var(--sigma-text-muted)" }}>Devise</span></div>
          </div>
        ) : (
          <p>Chargement…</p>
        )}
      </div>

      <div className="sigma-card">
        <h3 className="sigma-card__title">Années scolaires</h3>
        <table className="sigma-table">
          <thead>
            <tr>
              <th>Année</th>
              <th>Début</th>
              <th>Fin</th>
              <th>Statut</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {years.map((y) => (
              <tr key={y.id}>
                <td>{y.label}</td>
                <td>{y.start_date}</td>
                <td>{y.end_date}</td>
                <td>
                  {y.is_archived ? (
                    <span className="sigma-badge sigma-badge--gray">Archivée</span>
                  ) : y.is_current ? (
                    <span className="sigma-badge sigma-badge--green">En cours</span>
                  ) : (
                    <span className="sigma-badge sigma-badge--blue">Planifiée</span>
                  )}
                </td>
                <td>
                  {!y.is_archived && (
                    <button className="sigma-btn sigma-btn--danger" onClick={() => archiveYear(y.id)}>
                      Clôturer
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {years.length === 0 && (
              <tr><td colSpan={5} className="sigma-empty">Aucune année scolaire.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="sigma-card">
        <h3 className="sigma-card__title">Créer une nouvelle année scolaire</h3>
        <form onSubmit={createYear}>
          <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr 1fr auto", alignItems: "end" }}>
            <div className="sigma-field" style={{ marginBottom: 0 }}>
              <label>Libellé (ex: 2027/2028)</label>
              <input className="sigma-input" required value={label} onChange={(e) => setLabel(e.target.value)} />
            </div>
            <div className="sigma-field" style={{ marginBottom: 0 }}>
              <label>Date de début</label>
              <input className="sigma-input" type="date" required value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="sigma-field" style={{ marginBottom: 0 }}>
              <label>Date de fin</label>
              <input className="sigma-input" type="date" required value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
            <button className="sigma-btn sigma-btn--primary" type="submit">Créer</button>
          </div>
        </form>
      </div>
    </div>
  );
}
