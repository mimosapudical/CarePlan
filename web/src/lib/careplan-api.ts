import { CreateCarePlanInputSchema, CreateCarePlanResponseSchema, CarePlanDetailSchema, CarePlanStatusResponseSchema, SearchCarePlansResponseSchema, type CreateCarePlanInput } from "./schemas";

export class ApiError extends Error { constructor(message: string, public status: number) { super(message); } }
async function json<T>(response: Response, parse: (value: unknown) => T): Promise<T> {
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body && typeof body === "object" && "error" in body ? String(body.error) : `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }
  return parse(body);
}
export async function createCarePlan(input: CreateCarePlanInput) {
  const body = CreateCarePlanInputSchema.parse(input);
  return json(await fetch("/api/care-plans", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) }), (x) => CreateCarePlanResponseSchema.parse(x));
}
export async function getCarePlan(id: string) { return json(await fetch(`/api/care-plans/${encodeURIComponent(id)}`, { cache: "no-store" }), (x) => CarePlanDetailSchema.parse(x)); }
export async function getCarePlanStatus(id: string) { return json(await fetch(`/api/care-plans/${encodeURIComponent(id)}/status`, { cache: "no-store" }), (x) => CarePlanStatusResponseSchema.parse(x)); }
export async function searchCarePlans(query: string) { return json(await fetch(`/api/care-plans/search?q=${encodeURIComponent(query)}`, { cache: "no-store" }), (x) => SearchCarePlansResponseSchema.parse(x)); }
export const getCarePlanDownloadUrl = (id: string) => `/api/care-plans/${encodeURIComponent(id)}/download`;
