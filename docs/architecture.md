# Architecture

CarePlan is a small backend for pharmacy care-plan generation. Domain logic lives under `careplans/`. Runtime adapters differ by environment; the product behavior is the same: accept an order, generate asynchronously, expose status.

## Runtime shapes

### Local / Docker

```
Client → Django (web) → PostgreSQL
                ↓
              Celery → Redis queue → Celery worker → LLM → PostgreSQL
Client → Django status / detail endpoints ← PostgreSQL
```

- **Django** handles HTTP, validation, persistence, and enqueue.
- **Celery + Redis** decouple LLM work from the request thread.
- **PostgreSQL** stores providers, patients, orders, and care-plan status/content.

### AWS practice stack (`infra/practice/`)

```
Client → API Gateway
           ├─ POST /orders      → Lambda create_order → PostgreSQL (RDS)
           │                              ↓
           │                             SQS (+ DLQ)
           │                              ↓
           │                    Lambda generate_careplan → PostgreSQL + LLM
           └─ GET /orders/{id}  → Lambda get_order → PostgreSQL
```

| Component | Role |
|-----------|------|
| API Gateway (HTTP API) | Public entry for create and get |
| `create_order` Lambda | Persist order / enqueue work |
| SQS | Buffer between accept and generate; DLQ after repeated failures |
| `generate_careplan` Lambda | SQS-triggered generation worker |
| `get_order` Lambda | Read status / result |
| RDS PostgreSQL | Shared database |

`generate_careplan` is **not** exposed on API Gateway; it is invoked only via the SQS event source mapping.

## Request flow (happy path)

1. Client `POST`s an order (Django `/api/care-plans/` locally, or API Gateway `/orders` on AWS).
2. Create path writes a pending record and enqueues work (Celery task or SQS message).
3. Client receives an immediate acceptance response (local API returns `202` with an id).
4. Worker / generate Lambda processes the job, updates status through processing → completed (or failed).
5. Client polls status (`/api/care-plans/<id>/status/` locally, or `GET /orders/{id}` on the practice API) until terminal state.

## Shared domain

Application packages under `careplans/` (models, services, adapters, LLM abstraction) are intended to be reused across runtimes. Thin handlers under `runtimes/aws/` adapt AWS events to that domain. Stubs may still stand in for full Django packaging on Lambda until packaging is hardened.

## Related docs

- [deployment.md](deployment.md) — how to run each shape
- [tradeoffs.md](tradeoffs.md) — why async, Celery, Terraform
- [engineering-notes/day15.md](engineering-notes/day15.md) — IaC notes from Day 15
