import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { Post, UserOut } from "../../types";

export default function Users() {
  const { user } = useAuth();
  const [users, setUsers] = useState<UserOut[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    email: "", password: "", first_name: "", last_name: "", phone: "", post_ids: [] as string[],
  });

  const load = async () => {
    if (!user) return;
    try {
      const [usersRes, postsRes] = await Promise.all([
        api.get<UserOut[]>("/api/users", { params: { school_id: user.school_id } }),
        api.get<Post[]>(`/api/schools/${user.school_id}/posts`),
      ]);
      setUsers(usersRes.data);
      setPosts(postsRes.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const togglePost = (postId: string) => {
    setForm((f) => ({
      ...f,
      post_ids: f.post_ids.includes(postId) ? f.post_ids.filter((id) => id !== postId) : [...f.post_ids, postId],
    }));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    try {
      await api.post("/api/users", { ...form, school_id: user.school_id });
      setForm({ email: "", password: "", first_name: "", last_name: "", phone: "", post_ids: [] });
      setShowForm(false);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const toggleActive = async (u: UserOut) => {
    try {
      await api.patch(`/api/users/${u.id}`, { is_active: !u.is_active });
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-toolbar">
        <div />
        <button className="sigma-btn sigma-btn--primary" onClick={() => setShowForm(true)}>+ Nouvel utilisateur</button>
      </div>

      <div className="sigma-card">
        <table className="sigma-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>Téléphone</th>
              <th>Statut</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.first_name} {u.last_name} {u.is_superadmin && <span className="sigma-badge sigma-badge--blue">Superadmin</span>}</td>
                <td>{u.email}</td>
                <td>{u.phone ?? "—"}</td>
                <td>
                  {u.is_active ? (
                    <span className="sigma-badge sigma-badge--green">Actif</span>
                  ) : (
                    <span className="sigma-badge sigma-badge--red">Désactivé</span>
                  )}
                </td>
                <td>
                  <button className="sigma-btn sigma-btn--secondary" onClick={() => toggleActive(u)}>
                    {u.is_active ? "Désactiver" : "Réactiver"}
                  </button>
                </td>
              </tr>
            ))}
            {users.length === 0 && <tr><td colSpan={5} className="sigma-empty">Aucun utilisateur.</td></tr>}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="sigma-modal-backdrop" onClick={() => setShowForm(false)}>
          <div className="sigma-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nouvel utilisateur</h2>
            <form onSubmit={submit}>
              <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                <div className="sigma-field">
                  <label>Prénom</label>
                  <input className="sigma-input" required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
                </div>
                <div className="sigma-field">
                  <label>Nom</label>
                  <input className="sigma-input" required value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
                </div>
              </div>
              <div className="sigma-field">
                <label>Email</label>
                <input className="sigma-input" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
              <div className="sigma-field">
                <label>Téléphone</label>
                <input className="sigma-input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
              <div className="sigma-field">
                <label>Mot de passe temporaire</label>
                <input className="sigma-input" type="password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
              </div>
              <div className="sigma-field">
                <label>Poste(s)</label>
                {posts.map((p) => (
                  <label key={p.id} style={{ display: "block", fontWeight: 400, fontSize: 13, marginBottom: 4 }}>
                    <input type="checkbox" checked={form.post_ids.includes(p.id)} onChange={() => togglePost(p.id)} /> {p.name}
                  </label>
                ))}
                {posts.length === 0 && <p style={{ fontSize: 13, color: "var(--sigma-text-muted)" }}>Aucun poste défini. Créez-en un depuis "Postes & permissions".</p>}
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
