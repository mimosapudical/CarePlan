import { CarePlanStatusResponseSchema } from "@/lib/schemas";
import { djangoFetch, proxyJson, upstreamUnavailable } from "@/lib/server/django-client";
export const runtime = "nodejs";
export async function GET(_: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  try { return proxyJson(await djangoFetch(`/api/care-plans/${encodeURIComponent(id)}/status/`), CarePlanStatusResponseSchema); }
  catch { return upstreamUnavailable(); }
}
