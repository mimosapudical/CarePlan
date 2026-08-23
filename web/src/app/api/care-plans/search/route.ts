import { SearchCarePlansResponseSchema } from "@/lib/schemas";
import { djangoFetch, proxyJson, upstreamUnavailable } from "@/lib/server/django-client";
export const runtime = "nodejs";
export async function GET(request: Request) {
  const q = new URL(request.url).searchParams.get("q") ?? "";
  try { return proxyJson(await djangoFetch(`/api/care-plans/search/?q=${encodeURIComponent(q)}`), SearchCarePlansResponseSchema); }
  catch { return upstreamUnavailable(); }
}
