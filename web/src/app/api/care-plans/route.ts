import { CreateCarePlanInputSchema, CreateCarePlanResponseSchema } from "@/lib/schemas";
import { djangoFetch, proxyJson, upstreamUnavailable } from "@/lib/server/django-client";
import { NextResponse } from "next/server";
export const runtime = "nodejs";

export async function POST(request: Request) {
  const input = CreateCarePlanInputSchema.safeParse(await request.json().catch(() => null));
  if (!input.success) return NextResponse.json({ error: "Invalid care-plan request", details: input.error.flatten().fieldErrors }, { status: 400 });
  try {
    const response = await djangoFetch("/api/care-plans/", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(input.data) });
    if (response.status === 503) return NextResponse.json(await response.json().catch(() => ({ error: "Queue submission failed" })), { status: 503 });
    return proxyJson(response, CreateCarePlanResponseSchema, 202);
  } catch { return upstreamUnavailable(); }
}
