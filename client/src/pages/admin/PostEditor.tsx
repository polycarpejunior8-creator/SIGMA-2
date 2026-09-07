import React, { useEffect, useState } from "react";
import { SCOPE_TYPE_LABELS } from "../../types";
import type { Permission, Post, ScopeType } from "../../types";
import type { ScopeOptionsMap } from "../../hooks/useScopeOptions";

export interface ScopeAssignment {
  scope_type: ScopeType;
  scope_id: string | null;
}

export interface MatrixAssignment {
  permission_code: string;
  scopes: ScopeAssignment[];
}

interface Props {
  post: Post | null; // null = création
  permissions: Permission[];
  scopeOptions: ScopeOptionsMap;
  onClose: () => void;
  onSave: (name: string, description: string, assignments: MatrixAssignment[]) => Promise<void>;
}

const SCOPE_TYPES_WITH_VALUE: ScopeType[] = ["campus", "level", "stream", "class", "subject", "period"];

type MatrixState = Record<string, { enabled: boolean; scopes: ScopeAssignment[] }>;

function buildInitialMatrix(post: Post | null): MatrixState {
  const state: MatrixState = {};
  if (post) {
    for (const pp of post.post_permissions) {
      state[pp.permission.code] = {
        enabled: true,
        scopes: pp.scopes.map((s) => ({ scope_type: s.scope_type, scope_id: s.scope_id })),
      };
    }
  }
  return state;
}

export default function PostEditor({ post, permissions, scopeOptions, onClose, onSave }: Props) {
  const [name, setName] = useState(post?.name ?? "");
  const [description, setDescription] = useState(post?.description ?? "");
  const [matrix, setMatrix] = useState<MatrixState>(() => buildInitialMatrix(post));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // état local des sélecteurs "ajouter un périmètre" par permission
  const [pendingScopeType, setPendingScopeType] = useState<Record<string, ScopeType>>({});
  const [pendingScopeValue, setPendingScopeValue] = useState<Record<string, string>>({});

  useEffect(() => {
    setMatrix(buildInitialMatrix(post));
  }, [post]);

  const toggle = (code: string) => {
    setMatrix((m) => ({
      ...m,
      [code]: m[code]?.enabled ? { enabled: false, scopes: [] } : { enabled: true, scopes: [] },
    }));
  };

  const addScope = (code: string) => {
    const scopeType = pendingScopeType[code] ?? "school";
    const scopeValue = pendingScopeValue[code] ?? "";

    if (scopeType !== "school" && scopeType !== "own" && !scopeValue) return;

    setMatrix((m) => {
      const current = m[code] ?? { enabled: true, scopes: [] };
      const scopeId = scopeType === "school" || scopeType === "own" ? null : scopeValue;
      const alreadyExists = current.scopes.some((s) => s.scope_type === scopeType && s.scope_id === scopeId);
      if (alreadyExists) return m;
      return { ...m, [code]: { ...current, scopes: [...current.scopes, { scope_type: scopeType, scope_id: scopeId }] } };
    });
  };

  const removeScope = (code: string, index: number) => {
    setMatrix((m) => {
      const current = m[code];
      if (!current) return m;
      return { ...m, [code]: { ...current, scopes: current.scopes.filter((_, i) => i !== index) } };
    });
  };

  const scopeLabel = (scope: ScopeAssignment): string => {
    if (scope.scope_type === "school") return "Tout l'établissement";
    if (scope.scope_type === "own") return "Ses propres dossiers";
    const opt = scopeOptions[scope.scope_type]?.find((o) => o.id === scope.scope_id);
    return opt ? `${SCOPE_TYPE_LABELS[scope.scope_type]} : ${opt.name}` : `${SCOPE_TYPE_LABELS[scope.scope_type]} : ${scope.scope_id}`;
  };

  const grouped = permissions.reduce<Record<string, Permission[]>>((acc, p) => {
    (acc[p.module] ??= []).push(p);
    return acc;
  }, {});

  const submit = async () => {
    setError(null);
    if (!name.trim()) {
      setError("Le nom du poste est obligatoire.");
      return;
    }
    const entries: [string, { enabled: boolean; scopes: ScopeAssignment[] }][] = Object.entries(matrix);
    const assignments: MatrixAssignment[] = entries
      .filter(([, v]) => v.enabled)
      .map(([code, v]) => ({ permission_code: code, scopes: v.scopes }));

    setSaving(true);
    try {
      await onSave(name, description, assignments);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Erreur lors de l'enregistrement.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="sigma-modal-backdrop" onClick={onClose}>
      <div className="sigma-modal" style={{ width: 760 }} onClick={(e) => e.stopPropagation()}>
        <h2>{post ? `Modifier le poste : ${post.name}` : "Nouveau poste"}</h2>
        {post?.is_system && (
          <div className="sigma-error">Ce poste système n'est pas modifiable (lecture seule).</div>
        )}
        {error && <div className="sigma-error">{error}</div>}

        <div className="sigma-grid" style={{ gridTemplateColumns: "1fr 2fr" }}>
          <div className="sigma-field">
            <label>Nom du poste</label>
            <input className="sigma-input" value={name} disabled={post?.is_system} onChange={(e) => setName(e.target.value)} placeholder="ex: Responsable de la vie scolaire" />
          </div>
          <div className="sigma-field">
            <label>Description</label>
            <input className="sigma-input" value={description} disabled={post?.is_system} onChange={(e) => setDescription(e.target.value)} />
          </div>
        </div>

        <p style={{ fontSize: 13, color: "var(--sigma-text-muted)", marginTop: 0 }}>
          Cochez chaque permission accordée à ce poste. Sans périmètre ajouté, la permission
          s'applique à tout l'établissement. Ajoutez un ou plusieurs périmètres pour la restreindre
          (ex : "Saisir les notes" limité à "3e A" + "Mathématiques").
        </p>

        <table className="sigma-matrix">
          <thead>
            <tr>
              <th style={{ width: 28 }}></th>
              <th>Permission</th>
              <th>Périmètre</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(grouped).map(([module, perms]) => (
              <React.Fragment key={module}>
                <tr>
                  <td colSpan={3} className="sigma-matrix-module">{module}</td>
                </tr>
                {perms.map((perm) => {
                  const entry = matrix[perm.code];
                  const enabled = entry?.enabled ?? false;
                  return (
                    <tr key={perm.code}>
                      <td>
                        <input type="checkbox" disabled={post?.is_system} checked={enabled} onChange={() => toggle(perm.code)} />
                      </td>
                      <td>{perm.label_fr}</td>
                      <td>
                        {enabled && (
                          <>
                            {entry.scopes.map((s, i) => (
                              <span key={i} className="sigma-scope-tag">
                                {scopeLabel(s)}
                                {!post?.is_system && (
                                  <button
                                    type="button"
                                    onClick={() => removeScope(perm.code, i)}
                                    style={{ border: "none", background: "none", cursor: "pointer", color: "var(--sigma-red)" }}
                                  >
                                    ×
                                  </button>
                                )}
                              </span>
                            ))}
                            {entry.scopes.length === 0 && (
                              <span style={{ fontSize: 12, color: "var(--sigma-text-muted)" }}>Tout l'établissement</span>
                            )}
                            {!post?.is_system && (
                              <div style={{ display: "flex", gap: 4, marginTop: 6 }}>
                                <select
                                  className="sigma-select"
                                  style={{ width: 130 }}
                                  value={pendingScopeType[perm.code] ?? "school"}
                                  onChange={(e) => setPendingScopeType((s) => ({ ...s, [perm.code]: e.target.value as ScopeType }))}
                                >
                                  {(Object.keys(SCOPE_TYPE_LABELS) as ScopeType[]).map((st) => (
                                    <option key={st} value={st}>{SCOPE_TYPE_LABELS[st]}</option>
                                  ))}
                                </select>
                                {SCOPE_TYPES_WITH_VALUE.includes(pendingScopeType[perm.code] ?? "school") && (
                                  <select
                                    className="sigma-select"
                                    style={{ width: 160 }}
                                    value={pendingScopeValue[perm.code] ?? ""}
                                    onChange={(e) => setPendingScopeValue((s) => ({ ...s, [perm.code]: e.target.value }))}
                                  >
                                    <option value="">— choisir —</option>
                                    {(scopeOptions[pendingScopeType[perm.code] ?? "school"] ?? []).map((opt) => (
                                      <option key={opt.id} value={opt.id}>{opt.name}</option>
                                    ))}
                                  </select>
                                )}
                                <button type="button" className="sigma-btn sigma-btn--secondary" onClick={() => addScope(perm.code)}>
                                  + Ajouter
                                </button>
                              </div>
                            )}
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </React.Fragment>
            ))}
          </tbody>
        </table>

        <div className="sigma-modal__actions">
          <button type="button" className="sigma-btn sigma-btn--secondary" onClick={onClose}>Annuler</button>
          {!post?.is_system && (
            <button type="button" className="sigma-btn sigma-btn--primary" disabled={saving} onClick={submit}>
              {saving ? "Enregistrement…" : "Enregistrer"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
