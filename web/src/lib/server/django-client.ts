import "server-only";
import { NextResponse } from "next/server";
import type { ZodType } from "zod";

const baseUrl = process.env.DJANGO_API_BASE_URL ?? "http://127.0.0.1:8000";
export async function djangoFetch(path: string, init?: RequestInit) {
  return fetch(new URL(path, baseUrl), { ...init, cache: "no-store", signal: AbortSignal.timeout(10_000) });
}
export async function proxyJson(response: Response, schema: ZodType, successStatus = response.status) {
  const body: unknown = await response.json().catch(() => ({ error: "Invalid response from Django" }));
  if (!response.ok) return NextResponse.json(body, { status: response.status });
  const parsed = schema.safeParse(body);
  if (!parsed.success) return NextResponse.json({ error: "Django returned an invalid response" }, { status: 502 });
  return NextResponse.json(parsed.data, { status: successStatus });
}
export function upstreamUnavailable() { return NextResponse.json({ error: "Django service is unavailable" }, { status: 502 }); }
