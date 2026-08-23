"use client";
import { useState } from "react";
import { createCarePlan } from "@/lib/careplan-api";

const fields = [
  ["patient_first_name","Patient first name"],["patient_last_name","Patient last name"],["referring_provider","Referring provider"],
  ["referring_provider_npi","Provider NPI"],["patient_mrn","Patient MRN"],["patient_primary_diagnosis","Primary diagnosis"],
  ["medication_name","Medication"],["additional_diagnosis","Additional diagnoses"],["medication_history","Medication history"],
] as const;
export function CarePlanForm({ onAccepted }: { onAccepted: (id: string) => void }) {
  const [busy,setBusy] = useState(false); const [error,setError] = useState<string | null>(null);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return; setBusy(true); setError(null);
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try { const result = await createCarePlan(values as never); onAccepted(result.careplan_id); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Submission failed"); }
    finally { setBusy(false); }
  }
  return <form onSubmit={submit} className="form"><div className="form-grid">{fields.map(([name,label]) => <label key={name}><span>{label}</span><input name={name} required={name === "medication_name"} /></label>)}<label className="wide"><span>Patient records</span><textarea name="patient_records" rows={6} /></label></div>{error && <p role="alert" className="error">{error}</p>}<button className="button" disabled={busy}>{busy ? "Submitting…" : "Generate care plan"}</button></form>;
}
