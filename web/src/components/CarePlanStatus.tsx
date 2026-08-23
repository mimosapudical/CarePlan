import { getCarePlanDownloadUrl } from "@/lib/careplan-api";
import type { CarePlanStatusResponse } from "@/lib/schemas";
import { CarePlanContent } from "./CarePlanContent";
export function CarePlanStatus({ id, data, error }: { id: string | null; data: CarePlanStatusResponse | null; error: string | null }) {
  if (!id) return <p className="muted">Submit a request to begin.</p>;
  if (error) return <p role="alert" className="error">{error}</p>;
  const status = data?.status ?? "pending";
  return <div aria-live="polite"><p><span className={`badge ${status}`}>{status}</span> <code>{id}</code></p>{data?.error && <p role="alert" className="error">{data.error}</p>}{data?.content && <CarePlanContent content={data.content} />}{status === "completed" && <a className="button secondary" href={getCarePlanDownloadUrl(id)}>Download care plan</a>}</div>;
}
