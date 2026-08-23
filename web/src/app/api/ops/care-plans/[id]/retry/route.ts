import { OpsRetryResponseSchema } from "@/lib/schemas";
import { djangoFetch, proxyJson, upstreamUnavailable } from "@/lib/server/django-client";

export const runtime = "nodejs";

export async function POST(_: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  try {
    return proxyJson(
      await djangoFetch(`/api/ops/care-plans/${encodeURIComponent(id)}/retry/`, {
        method: "POST",
      }),
      OpsRetryResponseSchema,
      202,
    );
  } catch {
    return upstreamUnavailable();
  }
}
