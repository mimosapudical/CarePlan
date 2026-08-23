"use client";
import { useEffect, useState } from "react";
import { getCarePlanStatus } from "@/lib/careplan-api";
import type { CarePlanStatusResponse } from "@/lib/schemas";

export function useCarePlanPolling(id: string | null) {
  const [data, setData] = useState<CarePlanStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!id) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const next = await getCarePlanStatus(id);
        if (!active) return;
        setData(next); setError(null);
        if (next.status === "pending" || next.status === "processing") timer = setTimeout(poll, 3000);
      } catch (cause) { if (active) setError(cause instanceof Error ? cause.message : "Status request failed"); }
    };
    void poll();
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [id]);
  return { data, error };
}
