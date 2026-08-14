# ADR-0001: Keep an explicit OpenAPI contract for the existing Django API

Status: Accepted

## Context

CarePlan already has working Django function views and integration tests for the local HTTP API. The important client-facing behavior is spread across several files: `careplans/urls.py` defines the routes, `careplans/views.py` builds HTTP responses, `careplans/serializers.py` shapes payloads and records, `careplans/models.py` owns the care-plan states, and tests describe expected flows.

That layout is reasonable for a small Django application, but it leaves the HTTP contract implicit. A frontend or another service has to inspect Python implementation details to learn the available endpoints, accepted payload fields, response bodies, error shapes, status values, and the asynchronous submit-and-poll workflow. It also makes contract drift easy: a developer can change a serializer, status enum, or route and forget to update client documentation.

The goal of this change is API governance, not a handler architecture migration. Existing endpoints already work, and changing their implementation primarily to produce documentation would increase risk without changing the product behavior.

## Decision

Keep the current plain Django function views. Add a checked-in OpenAPI document for the existing Django API at `docs/openapi.yaml`, and add executable checks that validate the document and compare selected live Django responses against the documented schemas.

The OpenAPI file documents only routes that exist today:

- `POST /api/care-plans/`
- `GET /api/care-plans/search/`
- `GET /api/care-plans/{plan_id}/status/`
- `GET /api/care-plans/{plan_id}/download/`
- `GET /api/care-plans/{plan_id}/`

The contract intentionally reflects current behavior. Create payload fields are not marked required because the serializer supplies defaults. List-like fields document both arrays and comma-separated strings because the application accepts both. The successful create response documents the asynchronous `202 Accepted` shape, and queue submission failure documents the current serialized care-plan record returned with `503`.

CI now validates the OpenAPI document and runs the full test suite, including focused contract tests. The tests check for missing paths, invalid schema syntax, status enum drift from `CarePlan.STATUS_CHOICES`, response-field drift for status/detail/create responses, and the text media type for downloads.

## Alternatives considered

One alternative was rewriting the handlers into Django REST Framework `APIView`, `ViewSet`, and router patterns, then generating a schema from those handlers. That could make automatic schema generation easier over time. We rejected it for now because it would change already-working HTTP handlers mainly for documentation. It also mixes two independent changes: API architecture migration and API contract documentation. Combining those changes would make review harder and increase regression risk.

Another alternative was documentation only: add a hand-written OpenAPI file without executable checks. That would help readers initially, but it could silently become stale as routes, serializers, or model states change. Since contract drift is the failure mode we are trying to prevent, documentation without tests is not enough.

## Consequences

The positive result is that the Django API contract is explicit, reviewable in pull requests, usable by clients without reading Python source, and protected by CI. The existing handler architecture and application behavior are preserved, so this change stays focused on governance rather than runtime redesign.

The trade-off is that the OpenAPI document is maintained explicitly. When an API change is intentional, developers must update both the implementation and the contract. The contract tests make missed updates visible, but they do not remove the maintenance responsibility.

This decision also does not unify every runtime surface. The local Django API and the AWS API Gateway practice surface remain parallel APIs. Full cross-runtime contract unification may still be useful later, but it is separate from making the existing Django API explicit and checked today.
