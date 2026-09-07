import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { DashboardData } from "../types";

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api
      .get<DashboardData>(`/api/dashboard/${user.school_id}`)
      .then((res) => setData(res.data))
      .catch((err) => setError(apiErrorMessage(err)));
  }, [user]);

  if (error) return <div className="sigma-error">{error}</div>;
  if (!data) return <div className="sigma-empty">Chargement des indicateurs…</div>;

  const kpis = [
    { label: "Élèves actifs", value: data.active_students },
    { label: "Classes (année en cours)", value: data.classes_count },
    { label: "Moyenne générale", value: data.average_grade ?? "—" },
    { label: "Total encaissé", value: `${data.total_collected.toLocaleString("fr-FR")}` },
    { label: "Total dû", value: `${data.total_due.toLocaleString("fr-FR")}` },
    { label: "Impayés", value: `${data.unpaid_amount.toLocaleString("fr-FR")}` },
  ];

  return (
    <div>
      <div className="sigma-grid sigma-grid--kpi">
        {kpis.map((kpi) => (
          <div className="sigma-kpi" key={kpi.label}>
            <div className="sigma-kpi__value">{kpi.value}</div>
            <div className="sigma-kpi__label">{kpi.label}</div>
          </div>
        ))}
      </div>

      <div className="sigma-card">
        <h3 className="sigma-card__title">Bienvenue, {user?.first_name}</h3>
        <p style={{ color: "var(--sigma-text-muted)", fontSize: 14 }}>
          Vous êtes connecté avec le(s) poste(s) : <strong>{user?.posts.join(", ") || "aucun poste attribué"}</strong>.
          Le menu à gauche n'affiche que les sections auxquelles vos permissions vous donnent accès —
          c'est le moteur RBAC/Scopes de SIGMA qui construit cette interface pour vous.
        </p>
      </div>
    </div>
  );
}
