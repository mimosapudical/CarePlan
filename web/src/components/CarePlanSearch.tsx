"use client";
import Link from "next/link";
import { useState } from "react";
import { getCarePlanDownloadUrl, searchCarePlans } from "@/lib/careplan-api";
import type { CarePlanDetail } from "@/lib/schemas";
export function CarePlanSearch() {
  const [query,setQuery]=useState(""); const [results,setResults]=useState<CarePlanDetail[]>([]); const [busy,setBusy]=useState(false); const [error,setError]=useState<string|null>(null); const [searched,setSearched]=useState(false);
  async function submit(event: React.FormEvent) { event.preventDefault(); setBusy(true); setError(null); try { const data=await searchCarePlans(query.trim()); setResults(data.results); setSearched(true); } catch(cause){setError(cause instanceof Error?cause.message:"Search failed");} finally{setBusy(false);} }
  return <div><form className="search" onSubmit={submit}><label className="sr-only" htmlFor="query">Search care plans</label><input id="query" value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Patient, MRN, medication, or provider"/><button className="button" disabled={busy}>{busy?"Searching…":"Search"}</button></form>{error&&<p role="alert" className="error">{error}</p>}{searched&&results.length===0&&<p className="muted">No care plans found.</p>}<div className="results">{results.map((item)=>{const p=item.payload;const patient=[p.patient_first_name,p.patient_last_name].filter(Boolean).join(" ");return <article key={item.id} className="result-card"><div><strong>{String(patient||"Unnamed patient")}</strong><p>{String(p.patient_mrn??"")} · {String(p.medication_name??"")}</p></div><span className={`badge ${item.status}`}>{item.status}</span><div><Link href={`/care-plans/${item.id}`}>View</Link>{item.status==="completed"&&<> · <a href={getCarePlanDownloadUrl(item.id)}>Download</a></>}</div></article>;})}</div></div>;
}
