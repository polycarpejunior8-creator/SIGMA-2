import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { Student } from "../../types";

const STATUS_LABELS: Record<string, string> = {
  pre_enrolled: "Préinscrit", active: "Actif", transferred: "Transféré",
  graduated: "Diplômé", withdrawn: "Abandon", excluded: "Exclu",
};

export default function StudentsList() {
  const { user, can } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    matricule: "", first_name: "", last_name: "", date_of_birth: "", gender: "",
    guardian_first_name: "", guardian_last_name: "", guardian_phone: "", guardian_relationship: "père",
  });

  const load = async () => {
    if (!user) return;
    try {
      const res = await api.get<Student[]>("/api/students", { params: { school_id: user.school_id } });
      setStudents(res.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    try {
      const guardians = form.guardian_first_name
        ? [{
            school_id: user.school_id,
            first_name: form.guardian_first_name,
            last_name: form.guardian_last_name,
            phone: form.guardian_phone || null,
            relationship_type: form.guardian_relationship,
            is_primary_contact: true,
            can_pickup: true,
          }]
        : [];

      await api.post("/api/students", {
        school_id: user.school_id,
        matricule: form.matricule,
        first_name: form.first_name,
        last_name: form.last_name,
        date_of_birth: form.date_of_birth || null,
        gender: form.gender || null,
        guardians,
      });
      setShowForm(false);
      setForm({ matricule: "", first_name: "", last_name: "", date_of_birth: "", gender: "", guardian_first_name: "", guardian_last_name: "", guardian_phone: "", guardian_relationship: "père" });
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const filtered = students.filter((s) =>
    `${s.first_name} ${s.last_name} ${s.matricule}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-toolbar">
        <input className="sigma-input" style={{ maxWidth: 320 }} placeholder="Rechercher un élève…" value={search} onChange={(e) => setSearch(e.target.value)} />
        {can("students.create") && (
          <button className="sigma-btn sigma-btn--primary" onClick={() => setShowForm(true)}>+ Nouvel élève</button>
        )}
      </div>

      <div className="sigma-card">
        <table className="sigma-table">
          <thead>
            <tr><th>Matricule</th><th>Nom</th><th>Naissance</th><th>Statut</th><th></th></tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr key={s.id}>
                <td>{s.matricule}</td>
                <td>{s.first_name} {s.last_name}</td>
                <td>{s.date_of_birth ?? "—"}</td>
                <td><span className="sigma-badge sigma-badge--blue">{STATUS_LABELS[s.status] ?? s.status}</span></td>
                <td><Link className="sigma-btn sigma-btn--secondary" to={`/students/${s.id}`}>Ouvrir</Link></td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={5} className="sigma-empty">Aucun élève.</td></tr>}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="sigma-modal-backdrop" onClick={() => setShowForm(false)}>
          <div className="sigma-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nouvel élève</h2>
            <form onSubmit={submit}>
              <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                <div className="sigma-field">
                  <label>Matricule</label>
                  <input className="sigma-input" required value={form.matricule} onChange={(e) => setForm({ ...form, matricule: e.target.value })} />
                </div>
                <div className="sigma-field">
                  <label>Genre</label>
                  <select className="sigma-select" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
                    <option value="">—</option>
                    <option value="M">Masculin</option>
                    <option value="F">Féminin</option>
                  </select>
                </div>
                <div className="sigma-field">
                  <label>Prénom</label>
                  <input className="sigma-input" required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
                </div>
                <div className="sigma-field">
                  <label>Nom</label>
                  <input className="sigma-input" required value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
                </div>
                <div className="sigma-field">
                  <label>Date de naissance</label>
                  <input className="sigma-input" type="date" value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} />
                </div>
              </div>

              <h3 style={{ fontSize: 14 }}>Responsable (optionnel)</h3>
              <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                <div className="sigma-field">
                  <label>Prénom</label>
                  <input className="sigma-input" value={form.guardian_first_name} onChange={(e) => setForm({ ...form, guardian_first_name: e.target.value })} />
                </div>
                <div className="sigma-field">
                  <label>Nom</label>
                  <input className="sigma-input" value={form.guardian_last_name} onChange={(e) => setForm({ ...form, guardian_last_name: e.target.value })} />
                </div>
                <div className="sigma-field">
                  <label>Téléphone</label>
                  <input className="sigma-input" value={form.guardian_phone} onChange={(e) => setForm({ ...form, guardian_phone: e.target.value })} />
                </div>
                <div className="sigma-field">
                  <label>Relation</label>
                  <select className="sigma-select" value={form.guardian_relationship} onChange={(e) => setForm({ ...form, guardian_relationship: e.target.value })}>
                    <option value="père">Père</option>
                    <option value="mère">Mère</option>
                    <option value="tuteur">Tuteur</option>
                    <option value="autre">Autre</option>
                  </select>
                </div>
              </div>

              <div className="sigma-modal__actions">
                <button type="button" className="sigma-btn sigma-btn--secondary" onClick={() => setShowForm(false)}>Annuler</button>
                <button type="submit" className="sigma-btn sigma-btn--primary">Créer</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
