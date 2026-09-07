import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { SCOPE_TYPE_LABELS } from "../../types";
import type { Delegation, Permission, ScopeType, UserOut } from "../../types";

export default function Delegations() {
  const { user } = useAuth();
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [users, setUsers] = useState<UserOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    granted_to_id: "", permission_code: "", scope_type: "school" as ScopeType,
    reason: "", start_at: "", end_at: "",
  });

  const load = async () => {
    if (!user) return;
    try {
      const [delRes, permRes, usersRes] = await Promise.all([
        api.get<Delegation[]>("/api/delegations", { params: { school_id: user.school_id } }),
        api.get<Permission[]>("/api/permissions"),
        api.get<UserOut[]>("/api/users", { params: { school_id: user.school_id } }),
      ]);
      setDelegations(delRes.data);
      setPermissions(permRes.data);
      setUsers(usersRes.data);
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
      await api.post("/api/delegations", {
        school_id: user.school_id,
        granted_to_id: form.granted_to_id,
        permission_code: form.permission_code,
        scope_type: form.scope_type,
        reason: form.reason || null,
        start_at: new Date(form.start_at).toISOString(),
        end_at: new Date(form.end_at).toISOString(),
      });
      setShowForm(false);
      setForm({ granted_to_id: "", permission_code: "", scope_type: "school", reason: "", start_at: "", end_at: "" });
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const revoke = async (id: string) => {
    if (!confirm("Révoquer cette délégation immédiatement ?")) return;
    try {
      await api.post(`/api/delegations/${id}/revoke`);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const userLabel = (id: string) => {
    const u = users.find((x) => x.id === id);
    return u ? `${u.first_name} ${u.last_name}` : id;
  };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-toolbar">
        <p style={{ margin: 0, fontSize: 13, color: "var(--sigma-text-muted)", maxWidth: 560 }}>
          Ex : "Mme X absente. Le directeur accorde à M. Y la saisie des notes de mathématiques
          de 3e A du 10/09/2026 au 15/09/2026." La permission expire automatiquement (cf §13).
        </p>
        <button className="sigma-btn sigma-btn--primary" onClick={() => setShowForm(true)}>+ Nouvelle délégation</button>
      </div>

      <div className="sigma-card">
        <table className="sigma-table">
          <thead>
            <tr>
              <th>Bénéficiaire</th>
              <th>Permission</th>
              <th>Périmètre</th>
              <th>Du</th>
              <th>Au</th>
              <th>Statut</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {delegations.map((d) => {
              const now = new Date();
              const active = !d.is_revoked && new Date(d.start_at) <= now && now <= new Date(d.end_at);
              const expired = !d.is_revoked && now > new Date(d.end_at);
              return (
                <tr key={d.id}>
                  <td>{userLabel(d.granted_to_id)}</td>
                  <td>{permissions.find((p) => p.code === d.permission_code)?.label_fr ?? d.permission_code}</td>
                  <td>{SCOPE_TYPE_LABELS[d.scope_type]}</td>
                  <td>{new Date(d.start_at).toLocaleString("fr-FR")}</td>
                  <td>{new Date(d.end_at).toLocaleString("fr-FR")}</td>
                  <td>
                    {d.is_revoked ? (
                      <span className="sigma-badge sigma-badge--red">Révoquée</span>
                    ) : expired ? (
                      <span className="sigma-badge sigma-badge--gray">Expirée</span>
                    ) : active ? (
                      <span className="sigma-badge sigma-badge--green">Active</span>
                    ) : (
                      <span className="sigma-badge sigma-badge--orange">À venir</span>
                    )}
                  </td>
                  <td>
                    {!d.is_revoked && (
                      <button className="sigma-btn sigma-btn--danger" onClick={() => revoke(d.id)}>Révoquer</button>
                    )}
                  </td>
                </tr>
              );
            })}
            {delegations.length === 0 && <tr><td colSpan={7} className="sigma-empty">Aucune délégation.</td></tr>}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="sigma-modal-backdrop" onClick={() => setShowForm(false)}>
          <div className="sigma-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nouvelle délégation temporaire</h2>
            <form onSubmit={submit}>
              <div className="sigma-field">
                <label>Bénéficiaire</label>
                <select className="sigma-select" required value={form.granted_to_id} onChange={(e) => setForm({ ...form, granted_to_id: e.target.value })}>
                  <option value="">— choisir —</option>
                  {users.map((u) => <option key={u.id} value={u.id}>{u.first_name} {u.last_name}</option>)}
                </select>
              </div>
              <div className="sigma-field">
                <label>Permission déléguée</label>
                <select className="sigma-select" required value={form.permission_code} onChange={(e) => setForm({ ...form, permission_code: e.target.value })}>
                  <option value="">— choisir —</option>
                  {permissions.map((p) => <option key={p.id} value={p.code}>{p.label_fr}</option>)}
                </select>
              </div>
              <div className="sigma-field">
                <label>Motif</label>
                <input className="sigma-input" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} placeholder="ex: Mme X absente" />
              </div>
              <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                <div className="sigma-field">
                  <label>Début</label>
                  <input className="sigma-input" type="datetime-local" required value={form.start_at} onChange={(e) => setForm({ ...form, start_at: e.target.value })} />
                </div>
                <div className="sigma-field">
                  <label>Fin</label>
                  <input className="sigma-input" type="datetime-local" required value={form.end_at} onChange={(e) => setForm({ ...form, end_at: e.target.value })} />
                </div>
              </div>
              <div className="sigma-modal__actions">
                <button type="button" className="sigma-btn sigma-btn--secondary" onClick={() => setShowForm(false)}>Annuler</button>
                <button type="submit" className="sigma-btn sigma-btn--primary">Créer la délégation</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
