import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { AuditLog } from "../../types";

export default function AuditLogPage() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api
      .get<AuditLog[]>("/api/audit-logs", { params: { school_id: user.school_id, limit: 200 } })
      .then((res) => setLogs(res.data))
      .catch((err) => setError(apiErrorMessage(err)));
  }, [user]);

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}
      <div className="sigma-card">
        <p style={{ fontSize: 13, color: "var(--sigma-text-muted)", marginTop: 0 }}>
          Ce journal est en lecture seule : aucune opération sensible ne peut être modifiée ou supprimée par un
          utilisateur ordinaire (cf §14).
        </p>
        <table className="sigma-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Utilisateur</th>
              <th>Action</th>
              <th>Entité</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <React.Fragment key={log.id}>
                <tr>
                  <td>{new Date(log.created_at).toLocaleString("fr-FR")}</td>
                  <td>{log.user_label ?? "Système"}</td>
                  <td><span className="sigma-badge sigma-badge--blue">{log.action}</span></td>
                  <td>{log.entity_type} {log.entity_id ? `#${log.entity_id.slice(0, 8)}` : ""}</td>
                  <td>
                    {(log.old_value || log.new_value) && (
                      <button
                        className="sigma-btn sigma-btn--secondary"
                        onClick={() => setExpanded(expanded === log.id ? null : log.id)}
                      >
                        {expanded === log.id ? "Masquer" : "Détails"}
                      </button>
                    )}
                  </td>
                </tr>
                {expanded === log.id && (
                  <tr>
                    <td colSpan={5}>
                      <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                        <div>
                          <strong>Ancienne valeur</strong>
                          <pre style={{ fontSize: 12, background: "#f4f6f9", padding: 10, borderRadius: 6 }}>
                            {JSON.stringify(log.old_value, null, 2) || "—"}
                          </pre>
                        </div>
                        <div>
                          <strong>Nouvelle valeur</strong>
                          <pre style={{ fontSize: 12, background: "#f4f6f9", padding: 10, borderRadius: 6 }}>
                            {JSON.stringify(log.new_value, null, 2) || "—"}
                          </pre>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
            {logs.length === 0 && <tr><td colSpan={5} className="sigma-empty">Aucune entrée dans le journal.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
