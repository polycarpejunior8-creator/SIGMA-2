import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { useScopeOptions } from "../../hooks/useScopeOptions";
import type { Permission, Post } from "../../types";
import PostEditor, { MatrixAssignment } from "./PostEditor";

export default function Posts() {
  const { user } = useAuth();
  const [posts, setPosts] = useState<Post[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Post | null | "new">(null);

  const { options: scopeOptions } = useScopeOptions(user?.school_id);

  const load = async () => {
    if (!user) return;
    try {
      const [postsRes, permsRes] = await Promise.all([
        api.get<Post[]>(`/api/schools/${user.school_id}/posts`),
        api.get<Permission[]>("/api/permissions"),
      ]);
      setPosts(postsRes.data);
      setPermissions(permsRes.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleSave = async (name: string, description: string, assignments: MatrixAssignment[]) => {
    if (!user) return;
    if (editing === "new") {
      await api.post("/api/posts", { school_id: user.school_id, name, description, permissions: assignments });
    } else if (editing) {
      await api.patch(`/api/posts/${editing.id}`, { name, description, permissions: assignments });
    }
    setEditing(null);
    load();
  };

  const deletePost = async (post: Post) => {
    if (!confirm(`Supprimer le poste "${post.name}" ?`)) return;
    try {
      await api.delete(`/api/posts/${post.id}`);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-toolbar">
        <p style={{ margin: 0, fontSize: 13, color: "var(--sigma-text-muted)", maxWidth: 560 }}>
          Les postes de responsabilité sont créés et configurés ici, sans intervention du
          développeur (cf. §55 — règle d'or de SIGMA). Chaque permission peut être restreinte
          à un périmètre précis.
        </p>
        <button className="sigma-btn sigma-btn--primary" onClick={() => setEditing("new")}>+ Nouveau poste</button>
      </div>

      <div className="sigma-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
        {posts.map((post) => (
          <div className="sigma-card" key={post.id} style={{ marginBottom: 0 }}>
            <h3 className="sigma-card__title">
              {post.name} {post.is_system && <span className="sigma-badge sigma-badge--gray">Système</span>}
            </h3>
            <p style={{ fontSize: 13, color: "var(--sigma-text-muted)", minHeight: 34 }}>{post.description || "—"}</p>
            <p style={{ fontSize: 13 }}>{post.post_permissions.length} permission(s) accordée(s)</p>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="sigma-btn sigma-btn--secondary" onClick={() => setEditing(post)}>
                {post.is_system ? "Voir" : "Configurer"}
              </button>
              {!post.is_system && (
                <button className="sigma-btn sigma-btn--danger" onClick={() => deletePost(post)}>Supprimer</button>
              )}
            </div>
          </div>
        ))}
        {posts.length === 0 && <div className="sigma-empty">Aucun poste défini pour cet établissement.</div>}
      </div>

      {editing !== null && (
        <PostEditor
          post={editing === "new" ? null : editing}
          permissions={permissions}
          scopeOptions={scopeOptions}
          onClose={() => setEditing(null)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
