import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { Contract, ContractType, LeaveRecord, PayrollEntry, UserOut } from "../../types";

const CONTRACT_LABELS: Record<ContractType, string> = {
  cdi: "CDI", cdd: "CDD", vacation: "Vacataire", internship: "Stage",
};

export default function Staff() {
  const { user, can } = useAuth();
  const [staff, setStaff] = useState<UserOut[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [leave, setLeave] = useState<LeaveRecord[]>([]);
  const [payroll, setPayroll] = useState<PayrollEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [contractForm, setContractForm] = useState({ contract_type: "cdi" as ContractType, start_date: "", base_salary: 0 });
  const [leaveForm, setLeaveForm] = useState({ leave_type: "Congé annuel", start_date: "", end_date: "", reason: "" });
  const [payrollForm, setPayrollForm] = useState({ period_label: "", base_salary: 0, bonuses: 0, allowances: 0, deductions: 0 });

  useEffect(() => {
    if (!user) return;
    api.get<UserOut[]>("/api/users", { params: { school_id: user.school_id } }).then((r) => setStaff(r.data)).catch((err) => setError(apiErrorMessage(err)));
  }, [user]);

  const loadDetails = async (userId: string) => {
    try {
      const [contractsRes, leaveRes, payrollRes] = await Promise.all([
        api.get<Contract[]>(`/api/users/${userId}/contracts`),
        api.get<LeaveRecord[]>(`/api/users/${userId}/leave`),
        api.get<PayrollEntry[]>(`/api/users/${userId}/payroll`),
      ]);
      setContracts(contractsRes.data);
      setLeave(leaveRes.data);
      setPayroll(payrollRes.data);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  useEffect(() => {
    if (selectedId) loadDetails(selectedId);
  }, [selectedId]);

  const createContract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !selectedId) return;
    try {
      await api.post("/api/contracts", { user_id: selectedId, school_id: user.school_id, ...contractForm });
      loadDetails(selectedId);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const requestLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedId) return;
    try {
      await api.post("/api/leave-requests", { user_id: selectedId, ...leaveForm });
      loadDetails(selectedId);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const decideLeave = async (leaveId: string, approve: boolean) => {
    try {
      await api.post(`/api/leave-requests/${leaveId}/decision`, { approve });
      loadDetails(selectedId);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const createPayroll = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedId) return;
    try {
      await api.post("/api/payroll-entries", { user_id: selectedId, ...payrollForm });
      loadDetails(selectedId);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-card">
        <div className="sigma-field">
          <label>Membre du personnel</label>
          <select className="sigma-select" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
            <option value="">— choisir —</option>
            {staff.map((s) => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}
          </select>
        </div>
      </div>

      {selectedId && (
        <>
          <div className="sigma-card">
            <h3 className="sigma-card__title">Contrats</h3>
            <table className="sigma-table">
              <thead><tr><th>Type</th><th>Début</th><th>Fin</th><th>Salaire de base</th></tr></thead>
              <tbody>
                {contracts.map((c) => (
                  <tr key={c.id}><td>{CONTRACT_LABELS[c.contract_type]}</td><td>{c.start_date}</td><td>{c.end_date ?? "—"}</td><td>{c.base_salary}</td></tr>
                ))}
                {contracts.length === 0 && <tr><td colSpan={4} className="sigma-empty">Aucun contrat.</td></tr>}
              </tbody>
            </table>
            {can("hr.manage_contracts") && (
              <form onSubmit={createContract} style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                <select className="sigma-select" value={contractForm.contract_type} onChange={(e) => setContractForm({ ...contractForm, contract_type: e.target.value as ContractType })}>
                  {Object.entries(CONTRACT_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                <input className="sigma-input" type="date" required value={contractForm.start_date} onChange={(e) => setContractForm({ ...contractForm, start_date: e.target.value })} />
                <input className="sigma-input" type="number" placeholder="Salaire de base" value={contractForm.base_salary} onChange={(e) => setContractForm({ ...contractForm, base_salary: Number(e.target.value) })} />
                <button className="sigma-btn sigma-btn--primary" type="submit">Ajouter</button>
              </form>
            )}
          </div>

          <div className="sigma-card">
            <h3 className="sigma-card__title">Congés</h3>
            <table className="sigma-table">
              <thead><tr><th>Type</th><th>Du</th><th>Au</th><th>Statut</th><th></th></tr></thead>
              <tbody>
                {leave.map((l) => (
                  <tr key={l.id}>
                    <td>{l.leave_type}</td><td>{l.start_date}</td><td>{l.end_date}</td>
                    <td>
                      {l.status === "approved" && <span className="sigma-badge sigma-badge--green">Approuvé</span>}
                      {l.status === "rejected" && <span className="sigma-badge sigma-badge--red">Refusé</span>}
                      {l.status === "pending" && <span className="sigma-badge sigma-badge--orange">En attente</span>}
                    </td>
                    <td>
                      {l.status === "pending" && can("hr.approve_leave") && (
                        <div style={{ display: "flex", gap: 6 }}>
                          <button className="sigma-btn sigma-btn--secondary" onClick={() => decideLeave(l.id, true)}>Approuver</button>
                          <button className="sigma-btn sigma-btn--danger" onClick={() => decideLeave(l.id, false)}>Refuser</button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {leave.length === 0 && <tr><td colSpan={5} className="sigma-empty">Aucune demande de congé.</td></tr>}
              </tbody>
            </table>
            {can("hr.request_leave") && (
              <form onSubmit={requestLeave} style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                <input className="sigma-input" style={{ width: 160 }} value={leaveForm.leave_type} onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })} />
                <input className="sigma-input" type="date" required value={leaveForm.start_date} onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })} />
                <input className="sigma-input" type="date" required value={leaveForm.end_date} onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })} />
                <input className="sigma-input" style={{ flex: 1, minWidth: 160 }} placeholder="Motif" value={leaveForm.reason} onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })} />
                <button className="sigma-btn sigma-btn--primary" type="submit">Demander</button>
              </form>
            )}
          </div>

          {can("payroll.view") && (
            <div className="sigma-card">
              <h3 className="sigma-card__title">Fiches de paie</h3>
              <table className="sigma-table">
                <thead><tr><th>Période</th><th>Base</th><th>Primes</th><th>Indemnités</th><th>Retenues</th><th>Net à payer</th></tr></thead>
                <tbody>
                  {payroll.map((p) => (
                    <tr key={p.id}>
                      <td>{p.period_label}</td><td>{p.base_salary}</td><td>{p.bonuses}</td><td>{p.allowances}</td><td>{p.deductions}</td>
                      <td><strong>{p.net_pay}</strong></td>
                    </tr>
                  ))}
                  {payroll.length === 0 && <tr><td colSpan={6} className="sigma-empty">Aucune fiche de paie.</td></tr>}
                </tbody>
              </table>
              {can("payroll.manage") && (
                <form onSubmit={createPayroll} style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                  <input className="sigma-input" style={{ width: 120 }} placeholder="AAAA-MM" required value={payrollForm.period_label} onChange={(e) => setPayrollForm({ ...payrollForm, period_label: e.target.value })} />
                  <input className="sigma-input" style={{ width: 120 }} type="number" placeholder="Base" value={payrollForm.base_salary} onChange={(e) => setPayrollForm({ ...payrollForm, base_salary: Number(e.target.value) })} />
                  <input className="sigma-input" style={{ width: 120 }} type="number" placeholder="Primes" value={payrollForm.bonuses} onChange={(e) => setPayrollForm({ ...payrollForm, bonuses: Number(e.target.value) })} />
                  <input className="sigma-input" style={{ width: 120 }} type="number" placeholder="Indemnités" value={payrollForm.allowances} onChange={(e) => setPayrollForm({ ...payrollForm, allowances: Number(e.target.value) })} />
                  <input className="sigma-input" style={{ width: 120 }} type="number" placeholder="Retenues" value={payrollForm.deductions} onChange={(e) => setPayrollForm({ ...payrollForm, deductions: Number(e.target.value) })} />
                  <button className="sigma-btn sigma-btn--primary" type="submit">Générer</button>
                </form>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
