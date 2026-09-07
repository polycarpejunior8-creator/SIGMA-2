import React from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

interface NavItem {
  to: string;
  label: string;
  permission?: string; // si absent, visible par tous les utilisateurs connectés
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const SECTIONS: NavSection[] = [
  {
    title: "Pilotage",
    items: [{ to: "/", label: "Tableau de bord" }],
  },
  {
    title: "Élèves",
    items: [{ to: "/students", label: "Élèves", permission: "students.view" }],
  },
  {
    title: "Académique",
    items: [
      { to: "/academic/classes", label: "Classes & matières", permission: "classes.manage" },
      { to: "/academic/timetable", label: "Emploi du temps", permission: "timetable.view" },
      { to: "/academic/grades", label: "Évaluations & notes", permission: "grades.view" },
      { to: "/academic/life", label: "Vie scolaire", permission: "attendance.view" },
      { to: "/academic/honor-boards", label: "Tableaux d'honneur", permission: "honor_boards.view" },
    ],
  },
  {
    title: "Ressources humaines",
    items: [{ to: "/hr/staff", label: "Personnel & paie", permission: "hr.view_staff" }],
  },
  {
    title: "Finance",
    items: [{ to: "/finance", label: "Paiements & reçus", permission: "finance.view_payments" }],
  },
  {
    title: "Communication",
    items: [{ to: "/communication/announcements", label: "Annonces", permission: "communication.send" }],
  },
  {
    title: "Administration",
    items: [
      { to: "/admin/schools", label: "Établissement & années", permission: "schools.manage" },
      { to: "/admin/users", label: "Utilisateurs", permission: "users.view" },
      { to: "/admin/posts", label: "Postes & permissions", permission: "posts.manage" },
      { to: "/admin/delegations", label: "Délégations", permission: "delegations.manage" },
      { to: "/admin/audit", label: "Journal d'audit", permission: "audit.view" },
    ],
  },
];

const TITLES: Record<string, string> = {
  "/": "Tableau de bord",
  "/students": "Élèves",
  "/academic/classes": "Classes & matières",
  "/academic/timetable": "Emploi du temps",
  "/academic/grades": "Évaluations & notes",
  "/academic/life": "Vie scolaire",
  "/academic/honor-boards": "Tableaux d'honneur",
  "/hr/staff": "Personnel & paie",
  "/finance": "Paiements & reçus",
  "/communication/announcements": "Annonces",
  "/admin/schools": "Établissement & années scolaires",
  "/admin/users": "Utilisateurs",
  "/admin/posts": "Postes & permissions",
  "/admin/delegations": "Délégations temporaires",
  "/admin/audit": "Journal d'audit",
};

export default function AppShell() {
  const { user, can, logout } = useAuth();
  const location = useLocation();

  const title = TITLES[location.pathname] ?? "SIGMA";

  return (
    <div className="sigma-app-shell">
      <aside className="sigma-sidebar">
        <div className="sigma-sidebar__brand">
          SIGMA
          <small>Système Intégré de Gestion et Management Académique</small>
        </div>
        <nav className="sigma-sidebar__nav">
          {SECTIONS.map((section) => {
            const visibleItems = section.items.filter((item) => !item.permission || can(item.permission));
            if (visibleItems.length === 0) return null;
            return (
              <div key={section.title}>
                <div className="sigma-sidebar__section">{section.title}</div>
                {visibleItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) => "sigma-sidebar__link" + (isActive ? " active" : "")}
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            );
          })}
        </nav>
        <div className="sigma-sidebar__footer">
          <div style={{ fontWeight: 600 }}>{user?.first_name} {user?.last_name}</div>
          <div style={{ opacity: 0.6, marginBottom: 8 }}>{user?.posts.join(", ") || "Aucun poste"}</div>
          <button className="sigma-btn sigma-btn--secondary" style={{ width: "100%" }} onClick={logout}>
            Se déconnecter
          </button>
        </div>
      </aside>
      <div className="sigma-main">
        <header className="sigma-topbar">
          <div className="sigma-topbar__title">{title}</div>
        </header>
        <main className="sigma-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
