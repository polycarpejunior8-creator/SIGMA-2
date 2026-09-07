import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type {
  AcademicPeriod, AcademicYear, ClassGroup, HonorBoardOut, HonorBoardRule,
  HonorBoardScopeType, Level, Student,
} from "../../types";

export default function HonorBoards() {
  const { user, can } = useAuth();
  const [rules, setRules] = useState<HonorBoardRule[]>([]);
  const [levels, setLevels] = useState<Level[]>([]);
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [periods, setPeriods] = useState<AcademicPeriod[]>([]);
  const [students, setStudents] = useState<Record<string, Student>>({});
  const [board, setBoard] = useState<HonorBoardOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRuleForm, setShowRuleForm] = useState(false);

  const [ruleForm, setRuleForm] = useState({
    name: "", min_average: "", max_unjustified_absences: "", disallow_high_severity_sanction: true,
    weight_average: 100, weight_discipline: 0, weight_attendance: 0, weight_progression: 0, max_winners: "",
  });

  const [genForm, setGenForm] = useState({ rule_id: "", academic_period_id: "", scope_type: "class" as HonorBoardScopeType, class_id: "", level_id: "" });

  const load = async () => {
    if (!user) return;
    try {
      const [rulesRes, levelsRes, yearsRes] = await Promise.all([
        api.get<HonorBoardRule[]>(`/api/schools/${user.school_id}/honor-board-rules`),
        api.get<Level[]>(`/api/schools/${user.school_id}/levels`),
        api.get<AcademicYear[]>(`/api/schools/${user.school_id}/academic-years`),
      ]);
      setRules(rulesRes.data);
      setLevels(levelsRes.data);
      const current = yearsRes.data.find((y) => y.is_current);
      if (current) {
        const [classesRes, periodsRes] = await Promise.all([
          api.get<ClassGroup[]>(`/api/academic-years/${current.id}/classes`),
          api.get<AcademicPeriod[]>(`/api/academic-years/${current.id}/periods`),
        ]);
        setClasses(classesRes.data);
        setPeriods(periodsRes.data);
      }
      const studentsRes = await api.get<Student[]>("/api/students", { params: { school_id: user.school_id } });
      setStudents(Object.fromEntries(studentsRes.data.map((s) => [s.id, s])));
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const createRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    try {
      await api.post("/api/honor-board-rules", {
        school_id: user.school_id,
        name: ruleForm.name,
        min_average: ruleForm.min_average ? Number(ruleForm.min_average) : null,
        max_unjustified_absences: ruleForm.max_unjustified_absences ? Number(ruleForm.max_unjustified_absences) : null,
        disallow_high_severity_sanction: ruleForm.disallow_high_severity_sanction,
        weight_average: ruleForm.weight_average,
        weight_discipline: ruleForm.weight_discipline,
        weight_attendance: ruleForm.weight_attendance,
        weight_progression: ruleForm.weight_progression,
        max_winners: ruleForm.max_winners ? Number(ruleForm.max_winners) : null,
      });
      setShowRuleForm(false);
      load();
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const generate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const { data } = await api.post<HonorBoardOut>("/api/honor-boards/generate", {
        rule_id: genForm.rule_id,
        academic_period_id: genForm.academic_period_id,
        scope_type: genForm.scope_type,
        class_id: genForm.scope_type === "class" ? genForm.class_id : null,
        level_id: genForm.scope_type === "level" ? genForm.level_id : null,
      });
      setBoard(data);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const publish = async () => {
    if (!board) return;
    try {
      const { data } = await api.post<HonorBoardOut>(`/api/honor-boards/${board.id}/publish`);
      setBoard(data);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const weightSum = ruleForm.weight_average + ruleForm.weight_discipline + ruleForm.weight_attendance + ruleForm.weight_progression;

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-toolbar">
        <p style={{ margin: 0, fontSize: 13, color: "var(--sigma-text-muted)", maxWidth: 560 }}>
          Définissez vos règles (seuils et/ou pondération), puis générez le classement — SIGMA
          analyse automatiquement les résultats (cf §24).
        </p>
        {can("honor_boards.manage") && (
          <button className="sigma-btn sigma-btn--primary" onClick={() => setShowRuleForm(true)}>+ Nouvelle règle</button>
        )}
      </div>

      <div className="sigma-card">
        <h3 className="sigma-card__title">Règles configurées</h3>
        <table className="sigma-table">
          <thead><tr><th>Nom</th><th>Moy. min</th><th>Abs. max</th><th>Pondération</th><th>Top</th></tr></thead>
          <tbody>
            {rules.map((r) => (
              <tr key={r.id}>
                <td>{r.name}</td>
                <td>{r.min_average ?? "—"}</td>
                <td>{r.max_unjustified_absences ?? "—"}</td>
                <td>{r.weight_average}% moy. / {r.weight_discipline}% disc. / {r.weight_attendance}% assid.</td>
                <td>{r.max_winners ?? "Tous les éligibles"}</td>
              </tr>
            ))}
            {rules.length === 0 && <tr><td colSpan={5} className="sigma-empty">Aucune règle définie.</td></tr>}
          </tbody>
        </table>
      </div>

      {can("honor_boards.manage") && rules.length > 0 && (
        <div className="sigma-card">
          <h3 className="sigma-card__title">Générer un tableau</h3>
          <form onSubmit={generate}>
            <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
              <div className="sigma-field">
                <label>Règle</label>
                <select className="sigma-select" required value={genForm.rule_id} onChange={(e) => setGenForm({ ...genForm, rule_id: e.target.value })}>
                  <option value="">— choisir —</option>
                  {rules.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
                </select>
              </div>
              <div className="sigma-field">
                <label>Période</label>
                <select className="sigma-select" required value={genForm.academic_period_id} onChange={(e) => setGenForm({ ...genForm, academic_period_id: e.target.value })}>
                  <option value="">— choisir —</option>
                  {periods.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
                </select>
              </div>
              <div className="sigma-field">
                <label>Périmètre</label>
                <select className="sigma-select" value={genForm.scope_type} onChange={(e) => setGenForm({ ...genForm, scope_type: e.target.value as HonorBoardScopeType })}>
                  <option value="class">Une classe</option>
                  <option value="level">Un niveau</option>
                  <option value="school">Tout l'établissement</option>
                </select>
              </div>
            </div>
            {genForm.scope_type === "class" && (
              <div className="sigma-field">
                <label>Classe</label>
                <select className="sigma-select" required value={genForm.class_id} onChange={(e) => setGenForm({ ...genForm, class_id: e.target.value })}>
                  <option value="">— choisir —</option>
                  {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            )}
            {genForm.scope_type === "level" && (
              <div className="sigma-field">
                <label>Niveau</label>
                <select className="sigma-select" required value={genForm.level_id} onChange={(e) => setGenForm({ ...genForm, level_id: e.target.value })}>
                  <option value="">— choisir —</option>
                  {levels.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
                </select>
              </div>
            )}
            <button className="sigma-btn sigma-btn--primary" type="submit">Générer le classement</button>
          </form>
        </div>
      )}

      {board && (
        <div className="sigma-card">
          <div className="sigma-toolbar">
            <h3 className="sigma-card__title" style={{ margin: 0 }}>Résultat</h3>
            {can("honor_boards.manage") && !board.is_published && (
              <button className="sigma-btn sigma-btn--primary" onClick={publish}>Publier</button>
            )}
            {board.is_published && <span className="sigma-badge sigma-badge--green">Publié</span>}
          </div>
          <table className="sigma-table">
            <thead><tr><th>Rang</th><th>Élève</th><th>Moyenne</th><th>Abs. injustifiées</th><th>Score</th></tr></thead>
            <tbody>
              {board.entries.map((e) => (
                <tr key={e.student_id}>
                  <td>{e.rank}</td>
                  <td>{students[e.student_id] ? `${students[e.student_id].first_name} ${students[e.student_id].last_name}` : e.student_id}</td>
                  <td>{e.average}</td>
                  <td>{e.unjustified_absences}</td>
                  <td>{e.score}</td>
                </tr>
              ))}
              {board.entries.length === 0 && <tr><td colSpan={5} className="sigma-empty">Aucun élève éligible avec ces critères.</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {showRuleForm && (
        <div className="sigma-modal-backdrop" onClick={() => setShowRuleForm(false)}>
          <div className="sigma-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nouvelle règle de tableau d'honneur</h2>
            <form onSubmit={createRule}>
              <div className="sigma-field">
                <label>Nom (ex: Tableau d'excellence)</label>
                <input className="sigma-input" required value={ruleForm.name} onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })} />
              </div>
              <h3 style={{ fontSize: 14 }}>Seuils d'éligibilité (optionnels)</h3>
              <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                <div className="sigma-field">
                  <label>Moyenne minimale (/20)</label>
                  <input className="sigma-input" type="number" step="0.1" value={ruleForm.min_average} onChange={(e) => setRuleForm({ ...ruleForm, min_average: e.target.value })} />
                </div>
                <div className="sigma-field">
                  <label>Absences injustifiées max.</label>
                  <input className="sigma-input" type="number" value={ruleForm.max_unjustified_absences} onChange={(e) => setRuleForm({ ...ruleForm, max_unjustified_absences: e.target.value })} />
                </div>
              </div>
              <label style={{ display: "block", fontSize: 13, marginBottom: 14 }}>
                <input type="checkbox" checked={ruleForm.disallow_high_severity_sanction} onChange={(e) => setRuleForm({ ...ruleForm, disallow_high_severity_sanction: e.target.checked })} /> Exclure les élèves ayant une sanction grave
              </label>

              <h3 style={{ fontSize: 14 }}>Pondération du classement (doit sommer à 100)</h3>
              <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr 1fr 1fr" }}>
                <div className="sigma-field">
                  <label>Moyenne %</label>
                  <input className="sigma-input" type="number" value={ruleForm.weight_average} onChange={(e) => setRuleForm({ ...ruleForm, weight_average: Number(e.target.value) })} />
                </div>
                <div className="sigma-field">
                  <label>Discipline %</label>
                  <input className="sigma-input" type="number" value={ruleForm.weight_discipline} onChange={(e) => setRuleForm({ ...ruleForm, weight_discipline: Number(e.target.value) })} />
                </div>
                <div className="sigma-field">
                  <label>Assiduité %</label>
                  <input className="sigma-input" type="number" value={ruleForm.weight_attendance} onChange={(e) => setRuleForm({ ...ruleForm, weight_attendance: Number(e.target.value) })} />
                </div>
                <div className="sigma-field">
                  <label>Progression %</label>
                  <input className="sigma-input" type="number" value={ruleForm.weight_progression} onChange={(e) => setRuleForm({ ...ruleForm, weight_progression: Number(e.target.value) })} />
                </div>
              </div>
              {weightSum !== 100 && <div className="sigma-error">La somme des pondérations doit être égale à 100 (actuellement {weightSum}).</div>}

              <div className="sigma-field">
                <label>Nombre maximal de lauréats (vide = tous les éligibles)</label>
                <input className="sigma-input" type="number" value={ruleForm.max_winners} onChange={(e) => setRuleForm({ ...ruleForm, max_winners: e.target.value })} />
              </div>

              <div className="sigma-modal__actions">
                <button type="button" className="sigma-btn sigma-btn--secondary" onClick={() => setShowRuleForm(false)}>Annuler</button>
                <button type="submit" className="sigma-btn sigma-btn--primary" disabled={weightSum !== 100}>Créer</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
