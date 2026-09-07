import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiErrorMessage } from "../api/client";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="sigma-login-page">
      <form className="sigma-login-card" onSubmit={handleSubmit}>
        <h1>SIGMA</h1>
        <p className="subtitle">Centralisez. Automatisez. Pilotez.</p>

        {error && <div className="sigma-error">{error}</div>}

        <div className="sigma-field">
          <label>Adresse e-mail</label>
          <input
            className="sigma-input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@sigma.local"
            autoFocus
          />
        </div>

        <div className="sigma-field">
          <label>Mot de passe</label>
          <input
            className="sigma-input"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>

        <button className="sigma-btn sigma-btn--primary" style={{ width: "100%" }} disabled={submitting} type="submit">
          {submitting ? "Connexion…" : "Se connecter"}
        </button>
      </form>
    </div>
  );
}
