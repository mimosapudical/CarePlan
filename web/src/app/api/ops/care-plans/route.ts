import { NextResponse } from "next/server";
import { CarePlanStatusSchema, OpsCarePlanListResponseSchema } from "@/lib/schemas";
import { djangoFetch, proxyJson, upstreamUnavailable } from "@/lib/server/django-client";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const input = new URL(request.url).searchParams;
  const forwarded = new URLSearchParams();
  const status = input.get("status");
  const staleMinutes = input.get("stale_minutes");
  if (status) {
    if (!CarePlanStatusSchema.safeParse(status).success)
      return NextResponse.json({ error: "Invalid status" }, { status: 400 });
    forwarded.set("status", status);
  }
  if (staleMinutes !== null) {
    if (!/^[1-9][0-9]*$/.test(staleMinutes))
      return NextResponse.json({ error: "Invalid stale_minutes" }, { status: 400 });
    forwarded.set("stale_minutes", staleMinutes);
  }
  const query = forwarded.toString();
  try {
    return proxyJson(
      await djangoFetch(`/api/ops/care-plans/${query ? `?${query}` : ""}`),
      OpsCarePlanListResponseSchema,
    );
  } catch {
    return upstreamUnavailable();
  }
}
