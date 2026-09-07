import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { AcademicYear, Announcement, AnnouncementChannel, AnnouncementTarget, ClassGroup, Level } from "../../types";

const CHANNEL_LABELS: Record<AnnouncementChannel, string> = {
  in_app: "Application (immédiat)", sms: "SMS (à brancher)", email: "Email (à brancher)", push: "Notification push (à brancher)",
};

const TARGET_LABELS: Record<AnnouncementTarget, string> = {
  all: "Tout l'établissement", class: "Une classe", level: "Un niveau",
  guardians_unpaid: "Parents avec frais impayés", staff: "Personnel uniquement",
};

export default function Announcements() {
  const { user } = useAuth();
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [levels, setLevels] = useState<Level[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    title: "", body: "", channel: "in_app" as AnnouncementChannel, target: "all" as AnnouncementTarget,
    target_class_id: "", target_level_id: "",
  });

  const load = async () => {
    if (!user) return;
    try {
      const res = await api.get<Announcement[]>("/api/announcements", { params: { school_id: user.school_id } });
      setAnnouncements(res.data);
      const levelsRes = await api.get<Level[]>(`/api/schools/${user.school_id}/levels`);
      setLevels(levelsRes.data);
      const yearsRes = await api.get<AcademicYear[]>(`/api/schools/${user.school_id}/academic-years`);
      const current = yearsRes.data.find((y) => y.is_current);
      if (current) {
        const classesRes = await api.get<ClassGroup[]>(`/api/academic-years/${current.id}/classes`);
        setClasses(classesRes.data);
      }
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    try {
      await api.post("/api/announcements", {
        school_id: user.school_id,
        title: form.title, body: form.body, channel: form.channel, target: form.target,
        target_class_id: form.target === "class" ? form.target_class_id : null,
        target_level_id: form.target === "level" ? form.target_level_id : null,
      });
      setForm({ title: "", body: "", channel: "in_app", target: "all", target_class_id: "", target_level_id: "" });
      load();
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-card">
        <h3 className="sigma-card__title">Envoyer une annonce</h3>
        <p style={{ fontSize: 13, color: "var(--sigma-text-muted)", marginTop: 0 }}>
          Seul le canal "Application" est réellement délivré dans cette version — les canaux SMS/Email/Push
          nécessitent la configuration d'un fournisseur externe (cf §33).
        </p>
        <form onSubmit={submit}>
          <div className="sigma-field">
            <label>Titre</label>
            <input className="sigma-input" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div className="sigma-field">
            <label>Message</label>
            <textarea className="sigma-input" rows={3} required value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} />
          </div>
          <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div className="sigma-field">
              <label>Canal</label>
              <select className="sigma-select" value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value as AnnouncementChannel })}>
                {Object.entries(CHANNEL_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="sigma-field">
              <label>Destinataires</label>
              <select className="sigma-select" value={form.target} onChange={(e) => setForm({ ...form, target: e.target.value as AnnouncementTarget })}>
                {Object.entries(TARGET_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
          </div>
          {form.target === "class" && (
            <div className="sigma-field">
              <label>Classe</label>
              <select className="sigma-select" required value={form.target_class_id} onChange={(e) => setForm({ ...form, target_class_id: e.target.value })}>
                <option value="">— choisir —</option>
                {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          )}
          {form.target === "level" && (
            <div className="sigma-field">
              <label>Niveau</label>
              <select className="sigma-select" required value={form.target_level_id} onChange={(e) => setForm({ ...form, target_level_id: e.target.value })}>
                <option value="">— choisir —</option>
                {levels.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
          )}
          <button className="sigma-btn sigma-btn--primary" type="submit">Envoyer</button>
        </form>
      </div>

      <div className="sigma-card">
        <h3 className="sigma-card__title">Historique</h3>
        <table className="sigma-table">
          <thead><tr><th>Date</th><th>Titre</th><th>Destinataires</th><th>Canal</th><th>Statut</th></tr></thead>
          <tbody>
            {announcements.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.sent_at).toLocaleString("fr-FR")}</td>
                <td>{a.title}</td>
                <td>{TARGET_LABELS[a.target]}</td>
                <td>{CHANNEL_LABELS[a.channel]}</td>
                <td>{a.is_sent ? <span className="sigma-badge sigma-badge--green">Envoyée</span> : <span className="sigma-badge sigma-badge--orange">En attente d'intégration</span>}</td>
              </tr>
            ))}
            {announcements.length === 0 && <tr><td colSpan={5} className="sigma-empty">Aucune annonce.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
