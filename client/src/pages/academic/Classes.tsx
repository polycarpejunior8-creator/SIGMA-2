import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { AcademicYear, ClassGroup, Level, Stream, Subject } from "../../types";

export default function Classes() {
  const { user } = useAuth();
  const [levels, setLevels] = useState<Level[]>([]);
  const [streams, setStreams] = useState<Record<string, Stream[]>>({});
  const [currentYear, setCurrentYear] = useState<AcademicYear | null>(null);
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [newLevelName, setNewLevelName] = useState("");
  const [newClass, setNewClass] = useState({ level_id: "", name: "" });
  const [newSubject, setNewSubject] = useState({ code: "", name: "", default_coefficient: 1 });

  const load = async () => {
    if (!user) return;
    try {
      const levelsRes = await api.get<Level[]>(`/api/schools/${user.school_id}/levels`);
      setLevels(levelsRes.data);

      const streamsEntries = await Promise.all(
        levelsRes.data.map(async (lvl) => [lvl.id, (await api.get<Stream[]>(`/api/levels/${lvl.id}/streams`)).data] as const)
      );
      setStreams(Object.fromEntries(streamsEntries));

      const yearsRes = await api.get<AcademicYear[]>(`/api/schools/${user.school_id}/academic-years`);
      const current = yearsRes.data.find((y) => y.is_current) ?? null;
      setCurrentYear(current);
      if (current) {
        const classesRes = await api.get<ClassGroup[]>(`/api/academic-years/${current.id}/classes`);
        setClasses(classesRes.data);
      }

      const subjectsRes = await api.get<Subject[]>(`/api/schools/${user.school_id}/subjects`);
      setSubjects(subjectsRes.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const createLevel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    try {
      await api.post("/api/levels", { school_id: user.school_id, name: newLevelName, order_index: levels.length });
      setNewLevelName("");
      load();
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const createClass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentYear) return;
    try {
      await api.post("/api/classes", { academic_year_id: currentYear.id, level_id: newClass.level_id, name: newClass.name });
      setNewClass({ level_id: "", name: "" });
      load();
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const createSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    try {
      await api.post("/api/subjects", { school_id: user.school_id, ...newSubject });
      setNewSubject({ code: "", name: "", default_coefficient: 1 });
      load();
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}
      {!currentYear && <div className="sigma-error">Aucune année scolaire "en cours" n'est définie. Créez-en une depuis Établissement & années.</div>}

      <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="sigma-card">
          <h3 className="sigma-card__title">Niveaux</h3>
          <table className="sigma-table">
            <thead><tr><th>Niveau</th><th>Séries</th></tr></thead>
            <tbody>
              {levels.map((l) => (
                <tr key={l.id}>
                  <td>{l.name}</td>
                  <td>{(streams[l.id] ?? []).map((s) => s.name).join(", ") || "—"}</td>
                </tr>
              ))}
              {levels.length === 0 && <tr><td colSpan={2} className="sigma-empty">Aucun niveau.</td></tr>}
            </tbody>
          </table>
          <form onSubmit={createLevel} style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <input className="sigma-input" placeholder="Nom du niveau (ex: 3e)" required value={newLevelName} onChange={(e) => setNewLevelName(e.target.value)} />
            <button className="sigma-btn sigma-btn--primary" type="submit">Ajouter</button>
          </form>
        </div>

        <div className="sigma-card">
          <h3 className="sigma-card__title">Classes ({currentYear?.label ?? "—"})</h3>
          <table className="sigma-table">
            <thead><tr><th>Classe</th><th>Niveau</th></tr></thead>
            <tbody>
              {classes.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>{levels.find((l) => l.id === c.level_id)?.name ?? "—"}</td>
                </tr>
              ))}
              {classes.length === 0 && <tr><td colSpan={2} className="sigma-empty">Aucune classe.</td></tr>}
            </tbody>
          </table>
          {currentYear && (
            <form onSubmit={createClass} style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <select className="sigma-select" required value={newClass.level_id} onChange={(e) => setNewClass({ ...newClass, level_id: e.target.value })}>
                <option value="">Niveau</option>
                {levels.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
              <input className="sigma-input" placeholder="Nom (ex: 3e A)" required value={newClass.name} onChange={(e) => setNewClass({ ...newClass, name: e.target.value })} />
              <button className="sigma-btn sigma-btn--primary" type="submit">Ajouter</button>
            </form>
          )}
        </div>
      </div>

      <div className="sigma-card">
        <h3 className="sigma-card__title">Matières</h3>
        <table className="sigma-table">
          <thead><tr><th>Code</th><th>Nom</th><th>Coefficient par défaut</th></tr></thead>
          <tbody>
            {subjects.map((s) => (
              <tr key={s.id}><td>{s.code}</td><td>{s.name}</td><td>{s.default_coefficient}</td></tr>
            ))}
            {subjects.length === 0 && <tr><td colSpan={3} className="sigma-empty">Aucune matière.</td></tr>}
          </tbody>
        </table>
        <form onSubmit={createSubject} style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <input className="sigma-input" placeholder="Code (ex: MATH)" required value={newSubject.code} onChange={(e) => setNewSubject({ ...newSubject, code: e.target.value })} />
          <input className="sigma-input" placeholder="Nom" required value={newSubject.name} onChange={(e) => setNewSubject({ ...newSubject, name: e.target.value })} />
          <input className="sigma-input" type="number" step="0.5" style={{ width: 100 }} value={newSubject.default_coefficient} onChange={(e) => setNewSubject({ ...newSubject, default_coefficient: Number(e.target.value) })} />
          <button className="sigma-btn sigma-btn--primary" type="submit">Ajouter</button>
        </form>
      </div>
    </div>
  );
}
