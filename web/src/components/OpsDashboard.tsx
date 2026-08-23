"use client";

import { useCallback, useEffect, useState } from "react";
import { OpsCarePlanListResponseSchema, OpsRetryResponseSchema, type OpsCarePlan } from "@/lib/schemas";

function shortError(error: string | null) {
  return error ? error.replace(/[\r\n\t]+/g, " ").slice(0, 140) : "—";
}

function age(value: string | null) {
  if (!value) return "Unknown";
  const minutes = Math.max(0, Math.floor((Date.now() - Date.parse(value)) / 60_000));
  return minutes < 60 ? `${minutes}m ago` : `${Math.floor(minutes / 60)}h ago`;
}

export function OpsDashboard() {
  const [records, setRecords] = useState<OpsCarePlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ message: string; error: boolean } | null>(null);

  const refresh = useCallback(async () => {
    const response = await fetch("/api/ops/care-plans", { cache: "no-store" });
    const body: unknown = await response.json();
    if (!response.ok) {
      throw new Error(
        typeof body === "object" && body !== null && "error" in body
          ? String(body.error)
          : "Could not load operational jobs",
      );
    }
    setRecords(OpsCarePlanListResponseSchema.parse(body).results);
  }, []);

  useEffect(() => {
    let active = true;
    void Promise.resolve()
      .then(refresh)
      .catch((error: unknown) => {
        if (active) {
          setNotice({
            message: error instanceof Error ? error.message : "Could not load operational jobs",
            error: true,
          });
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refresh]);

  async function retry(id: string) {
    setRetrying(id);
    setNotice(null);
    try {
      const response = await fetch(`/api/ops/care-plans/${encodeURIComponent(id)}/retry`, {
        method: "POST",
      });
      const body: unknown = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof body === "object" && body !== null && "error" in body
            ? String(body.error)
            : `Retry failed (${response.status})`,
        );
      }
      OpsRetryResponseSchema.parse(body);
      await refresh();
      setNotice({ message: "Job successfully resubmitted to the queue.", error: false });
    } catch (error: unknown) {
      setNotice({
        message: error instanceof Error ? error.message : "Could not retry job",
        error: true,
      });
    } finally {
      setRetrying(null);
    }
  }

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">CarePlan operations</p>
        <h1>Keep asynchronous care-plan jobs moving.</h1>
        <p className="lede">Review failed and stale jobs without displaying patient information.</p>
      </header>
      <section className="panel">
        <h2>Queue overview</h2>
        <div className="ops-summary">
          <p><strong>{records.length}</strong> jobs returned</p>
          <p><strong>{records.filter((record) => record.status === "failed").length}</strong> failed</p>
          <p><strong>{records.filter((record) => record.stale).length}</strong> stale</p>
        </div>
        {notice && (
          <p role="status" className={notice.error ? "error" : undefined}>
            {notice.message}
          </p>
        )}
        {loading && <p className="muted">Loading operational jobs…</p>}
        {!loading && records.length === 0 && <p className="muted">No operational jobs found.</p>}
        <div className="results">
          {records.map((record) => (
            <article className="result-card" key={record.id}>
              <div>
                <p><code>{record.id}</code></p>
                <p>
                  <span className={`badge ${record.status}`}>{record.status}</span>
                  {record.stale && <span className="badge stale">stale</span>}
                </p>
                <p>Updated {age(record.updated_at)} · Retries: {record.manual_retry_count}</p>
                {record.error && <p className="error">{shortError(record.error)}</p>}
              </div>
              {record.status === "failed" && (
                <button
                  className="button"
                  disabled={retrying !== null}
                  onClick={() => void retry(record.id)}
                  type="button"
                >
                  {retrying === record.id ? "Retrying…" : "Retry"}
                </button>
              )}
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
