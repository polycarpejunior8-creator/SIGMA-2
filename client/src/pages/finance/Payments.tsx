import React, { useEffect, useState } from "react";
import { api, apiErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { AcademicYear, FeeStructure, Invoice, Payment, Student } from "../../types";

const METHOD_LABELS: Record<string, string> = {
  cash: "Espèces", bank_transfer: "Virement", cheque: "Chèque", mobile_money: "Mobile Money", other: "Autre",
};

export default function Payments() {
  const { user, can } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [feeStructures, setFeeStructures] = useState<FeeStructure[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payments, setPayments] = useState<Record<string, Payment[]>>({});
  const [error, setError] = useState<string | null>(null);

  const [newInvoice, setNewInvoice] = useState({ fee_structure_id: "", amount_due: 0 });
  const [paymentAmounts, setPaymentAmounts] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!user) return;
    api.get<Student[]>("/api/students", { params: { school_id: user.school_id } }).then((r) => setStudents(r.data));
    api.get<AcademicYear[]>(`/api/schools/${user.school_id}/academic-years`).then((r) => {
      const current = r.data.find((y) => y.is_current);
      if (current) {
        api.get<FeeStructure[]>(`/api/schools/${user.school_id}/fee-structures`).then((res) => setFeeStructures(res.data));
      }
    });
  }, [user]);

  const loadInvoices = async (studentId: string) => {
    try {
      const res = await api.get<Invoice[]>(`/api/students/${studentId}/invoices`);
      setInvoices(res.data);
      const paymentsEntries = await Promise.all(
        res.data.map(async (inv) => [inv.id, (await api.get<Payment[]>(`/api/invoices/${inv.id}/payments`)).data] as const)
      );
      setPayments(Object.fromEntries(paymentsEntries));
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  useEffect(() => {
    if (selectedStudentId) loadInvoices(selectedStudentId);
  }, [selectedStudentId]);

  const createInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudentId || !newInvoice.fee_structure_id) return;
    try {
      await api.post("/api/invoices", {
        student_id: selectedStudentId, fee_structure_id: newInvoice.fee_structure_id, amount_due: newInvoice.amount_due,
      });
      setNewInvoice({ fee_structure_id: "", amount_due: 0 });
      loadInvoices(selectedStudentId);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const recordPayment = async (invoiceId: string) => {
    const amount = Number(paymentAmounts[invoiceId] ?? 0);
    if (!amount) return;
    try {
      await api.post("/api/payments", { invoice_id: invoiceId, amount });
      setPaymentAmounts((p) => ({ ...p, [invoiceId]: "" }));
      loadInvoices(selectedStudentId);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const cancelPayment = async (paymentId: string) => {
    const reason = prompt("Motif de l'annulation :");
    if (!reason) return;
    try {
      await api.post(`/api/payments/${paymentId}/cancel`, { reason });
      loadInvoices(selectedStudentId);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const reprintReceipt = async (paymentId: string) => {
    try {
      await api.post(`/api/payments/${paymentId}/reprint`);
      loadInvoices(selectedStudentId);
    } catch (err) { setError(apiErrorMessage(err)); }
  };

  const totalPaid = (invoiceId: string) =>
    (payments[invoiceId] ?? []).filter((p) => !p.is_cancelled).reduce((sum, p) => sum + p.amount, 0);

  return (
    <div>
      {error && <div className="sigma-error">{error}</div>}

      <div className="sigma-card">
        <h3 className="sigma-card__title">Sélectionner un élève</h3>
        <select className="sigma-select" value={selectedStudentId} onChange={(e) => setSelectedStudentId(e.target.value)}>
          <option value="">— choisir —</option>
          {students.map((s) => <option key={s.id} value={s.id}>{s.first_name} {s.last_name} ({s.matricule})</option>)}
        </select>
      </div>

      {selectedStudentId && (
        <>
          {can("finance.manage_fee_structures") && (
            <div className="sigma-card">
              <h3 className="sigma-card__title">Créer une facture</h3>
              <form onSubmit={createInvoice} style={{ display: "flex", gap: 8 }}>
                <select
                  className="sigma-select"
                  value={newInvoice.fee_structure_id}
                  onChange={(e) => {
                    const fee = feeStructures.find((f) => f.id === e.target.value);
                    setNewInvoice({ fee_structure_id: e.target.value, amount_due: fee?.amount ?? 0 });
                  }}
                >
                  <option value="">— tarif —</option>
                  {feeStructures.map((f) => <option key={f.id} value={f.id}>{f.name} ({f.amount})</option>)}
                </select>
                <input className="sigma-input" style={{ width: 160 }} type="number" value={newInvoice.amount_due} onChange={(e) => setNewInvoice({ ...newInvoice, amount_due: Number(e.target.value) })} />
                <button className="sigma-btn sigma-btn--primary" type="submit">Créer la facture</button>
              </form>
            </div>
          )}

          {invoices.map((inv) => {
            const fee = feeStructures.find((f) => f.id === inv.fee_structure_id);
            const paid = totalPaid(inv.id);
            const balance = inv.amount_due - inv.discount_amount - paid;
            return (
              <div className="sigma-card" key={inv.id}>
                <div className="sigma-toolbar">
                  <h3 className="sigma-card__title" style={{ margin: 0 }}>{fee?.name ?? "Facture"} — dû {inv.amount_due}</h3>
                  <span className={"sigma-badge " + (balance <= 0 ? "sigma-badge--green" : "sigma-badge--orange")}>
                    {balance <= 0 ? "Soldé" : `Solde : ${balance}`}
                  </span>
                </div>

                <table className="sigma-table">
                  <thead><tr><th>Reçu</th><th>Montant</th><th>Méthode</th><th>Date</th><th>Statut</th><th></th></tr></thead>
                  <tbody>
                    {(payments[inv.id] ?? []).map((p) => (
                      <tr key={p.id}>
                        <td>{p.receipt_number} {p.reprint_count > 0 && <span className="sigma-badge sigma-badge--gray">Réimprimé ×{p.reprint_count}</span>}</td>
                        <td>{p.amount}</td>
                        <td>{METHOD_LABELS[p.method] ?? p.method}</td>
                        <td>{new Date(p.paid_at).toLocaleDateString("fr-FR")}</td>
                        <td>{p.is_cancelled ? <span className="sigma-badge sigma-badge--red">Annulé</span> : <span className="sigma-badge sigma-badge--green">Valide</span>}</td>
                        <td style={{ display: "flex", gap: 6 }}>
                          {can("finance.print_receipt") && <button className="sigma-btn sigma-btn--secondary" onClick={() => reprintReceipt(p.id)}>Réimprimer</button>}
                          {can("finance.cancel_payment") && !p.is_cancelled && <button className="sigma-btn sigma-btn--danger" onClick={() => cancelPayment(p.id)}>Annuler</button>}
                        </td>
                      </tr>
                    ))}
                    {(payments[inv.id] ?? []).length === 0 && <tr><td colSpan={6} className="sigma-empty">Aucun paiement.</td></tr>}
                  </tbody>
                </table>

                {can("finance.record_payment") && balance > 0 && (
                  <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                    <input
                      className="sigma-input" style={{ width: 160 }} type="number" placeholder="Montant"
                      value={paymentAmounts[inv.id] ?? ""}
                      onChange={(e) => setPaymentAmounts((p) => ({ ...p, [inv.id]: e.target.value }))}
                    />
                    <button className="sigma-btn sigma-btn--primary" onClick={() => recordPayment(inv.id)}>Enregistrer le paiement</button>
                  </div>
                )}
              </div>
            );
          })}
          {invoices.length === 0 && <div className="sigma-empty">Aucune facture pour cet élève.</div>}
        </>
      )}
    </div>
  );
}
