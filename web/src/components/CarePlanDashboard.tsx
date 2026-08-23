"use client";
import { useState } from "react";
import { useCarePlanPolling } from "@/hooks/useCarePlanPolling";
import { CarePlanForm } from "./CarePlanForm";
import { CarePlanSearch } from "./CarePlanSearch";
import { CarePlanStatus } from "./CarePlanStatus";
export function CarePlanDashboard(){const[id,setId]=useState<string|null>(null);const{data,error}=useCarePlanPolling(id);return <main className="shell"><header><p className="eyebrow">CarePlan workspace</p><h1>Turn pharmacy records into an actionable care plan.</h1><p className="lede">Submit once, continue working, and follow generation from the queue to a completed plan.</p></header><section className="panel"><h2>New care plan</h2><CarePlanForm onAccepted={setId}/></section><section className="panel"><h2>Generation status</h2><CarePlanStatus id={id} data={data} error={error}/></section><section className="panel"><h2>Find a care plan</h2><CarePlanSearch/></section></main>}
