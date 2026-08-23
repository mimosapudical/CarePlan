import { djangoFetch, upstreamUnavailable } from "@/lib/server/django-client";
import { NextResponse } from "next/server";
export const runtime = "nodejs";
export async function GET(_: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  try {
    const response = await djangoFetch(`/api/care-plans/${encodeURIComponent(id)}/download/`);
    if (!response.ok) return NextResponse.json(await response.json().catch(() => ({ error: "Download failed" })), { status: response.status });
    return new Response(response.body, { status: 200, headers: { "content-type": response.headers.get("content-type") ?? "text/plain; charset=utf-8", "content-disposition": response.headers.get("content-disposition") ?? `attachment; filename="care_plan_${id}.txt"` } });
  } catch { return upstreamUnavailable(); }
}
