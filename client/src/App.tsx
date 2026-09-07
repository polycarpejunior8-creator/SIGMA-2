import React from "react";
import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AppShell from "./components/AppShell";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Schools from "./pages/admin/Schools";
import Users from "./pages/admin/Users";
import Posts from "./pages/admin/Posts";
import Delegations from "./pages/admin/Delegations";
import AuditLogPage from "./pages/admin/AuditLog";
import Classes from "./pages/academic/Classes";
import Grades from "./pages/academic/Grades";
import Timetable from "./pages/academic/Timetable";
import LifeAtSchool from "./pages/academic/LifeAtSchool";
import HonorBoards from "./pages/academic/HonorBoards";
import StudentsList from "./pages/students/StudentsList";
import StudentDetail from "./pages/students/StudentDetail";
import Payments from "./pages/finance/Payments";
import Staff from "./pages/hr/Staff";
import Announcements from "./pages/communication/Announcements";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="students" element={<StudentsList />} />
        <Route path="students/:id" element={<StudentDetail />} />
        <Route path="academic/classes" element={<Classes />} />
        <Route path="academic/timetable" element={<Timetable />} />
        <Route path="academic/grades" element={<Grades />} />
        <Route path="academic/life" element={<LifeAtSchool />} />
        <Route path="academic/honor-boards" element={<HonorBoards />} />
        <Route path="finance" element={<Payments />} />
        <Route path="hr/staff" element={<Staff />} />
        <Route path="communication/announcements" element={<Announcements />} />
        <Route path="admin/schools" element={<Schools />} />
        <Route path="admin/users" element={<Users />} />
        <Route path="admin/posts" element={<Posts />} />
        <Route path="admin/delegations" element={<Delegations />} />
        <Route path="admin/audit" element={<AuditLogPage />} />
      </Route>
    </Routes>
  );
}
