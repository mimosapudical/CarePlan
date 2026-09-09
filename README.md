# CarePlan

Full-stack product that accepts pharmacy care-plan requests, generates plans asynchronously via an LLM, and exposes typed status and result workflows. A Next.js/TypeScript product interface uses Node.js route handlers as a backend-for-frontend over the existing Django domain API.

The same domain logic runs in three shapes:

- **Local / Docker** - Django + Celery + Redis + PostgreSQL
- **AWS practice stack** - API Gateway + Lambda + SQS + RDS (provisioned with Terraform)
- **Kubernetes** - Django -> ExecutionBackend -> CarePlanJob CR -> Go controller -> Kubernetes Job

## Runtime Comparison

| Runtime | Trigger model | Retry owner | Best fit |
| --- | --- | --- | --- |
| Celery | Queue consumption | Celery | local/simple async deployment |
| AWS | Queue/event | SQS/Lambda | serverless AWS deployment |
| Kubernetes | Desired-state reconciliation | Kubernetes Job | Kubernetes-hosted workloads |

## Architecture

The product request path is:

```text
Browser -> Next.js / TypeScript UI -> Node.js BFF -> Django API
                                                   -> PostgreSQL
                                                   -> ExecutionBackend -> Celery | Kubernetes
```

The browser calls same-origin Next.js routes. The Node layer validates Django responses with Zod, normalizes upstream failures, disables caching for mutable care-plan data, and forwards text downloads. Django remains the system of record and owns domain behavior.

Cloud request path (practice infrastructure under `infra/practice/`):

```mermaid
flowchart LR
  Client --> APIGW[API Gateway]
  APIGW -->|POST /orders| Create[Lambda create_order]
  Create --> SQS[(SQS)]
  Create --> PG[(PostgreSQL)]
  SQS --> Generate[Lambda generate_careplan]
  Generate --> PG
  APIGW -->|GET /orders/id| Get[Lambda get_order]
  Get --> PG
```

Locally, Celery + Redis play the same role as SQS + the generate worker. Kubernetes is an alternate execution adapter, not a replacement for Celery. See [docs/architecture.md](docs/architecture.md) for detail.

## Infrastructure

Cloud resources are defined as code with **Terraform** in `infra/practice/`:

| Resource | Purpose |
| --- | --- |
| API Gateway (HTTP API) | `POST /orders`, `GET /orders/{id}` |
| Lambda x 3 | create order, generate care plan, get order |
| SQS (+ DLQ) | Async handoff from create -> generate |
| RDS PostgreSQL | Shared persistence |

Apply and destroy from that directory (requires AWS credentials and `TF_VAR_db_password`). Full steps: [docs/deployment.md](docs/deployment.md).

**Cost note:** Practice cloud resources are created only for testing and intentionally destroyed afterward (`terraform destroy`) to avoid ongoing AWS charges. Do not leave the stack running idle.

## Documentation

| Doc | Contents |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | Backend shape and request flow |
| [docs/openapi.yaml](docs/openapi.yaml) | Client-facing Django HTTP contract |
| [docs/adr/0001-explicit-openapi-contract.md](docs/adr/0001-explicit-openapi-contract.md) | Why the contract is explicit and CI-checked |
| [docs/deployment.md](docs/deployment.md) | Docker local + Terraform cloud |
| [docs/tradeoffs.md](docs/tradeoffs.md) | Why these choices, limits, next steps |
| [care_plan_design_doc.md](care_plan_design_doc.md) | Product / domain design |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [docs/releases/v0.7.md](docs/releases/v0.7.md) | v0.7 release notes |
| [docs/engineering-notes/day15.md](docs/engineering-notes/day15.md) | Day 15 engineering notes |

## Local Run

Run the product interface after starting Django and Celery:

```bash
cd web
npm ci
npm run dev
```

Open `http://127.0.0.1:3000/`. The existing Django UI and API remain at `http://127.0.0.1:8000/`.

Terminal 1 (API):

```bash
pip install -r requirements.txt
set POSTGRES_DB=careplan
set POSTGRES_USER=careplan
set POSTGRES_PASSWORD=careplan
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Terminal 2 (Celery worker):

```bash
celery -A careplan_mvp worker --loglevel=info
```

Open `http://127.0.0.1:8000/` for the backend or legacy interface.

The default execution backend is Celery. To set it explicitly:

```bash
set CAREPLAN_EXECUTION_BACKEND=celery
```

## Docker Run

```bash
docker compose up --build
```

Starts Next.js `frontend` (`localhost:3000`), Django `web` (`localhost:8000`), the Spring read API (`localhost:8080`), Celery `worker`, PostgreSQL (`localhost:5432`), and Redis (`localhost:6379`).

GCP credentials: Compose mounts your Windows Application Default Credentials into `web`/`worker` and sets `GOOGLE_APPLICATION_CREDENTIALS`. Ensure `.env` has `GCP_PROJECT` / `GCP_LOCATION`, and that you once ran:

```bash
gcloud auth application-default login
```

TablePlus local connection:

- Host: `localhost`
- Port: `5432`
- Database: `careplan`
- User: `careplan`
- Password: `careplan`

## Incremental Spring Boot modernization

`spring-careplan-api/` is a Java 21 + Spring Boot 3 modernization slice that initially owns only read-heavy CarePlan paths. Reads are a low-risk first boundary because both implementations can query the same Django-owned PostgreSQL rows while responses are checked for contract parity. Django remains the source of truth for `create_care_plan`, background generation, Celery execution, retries, and all write-side business logic, so the migration does not create two competing writers.

The Spring service maps the existing `careplans_careplan` table, runs Hibernate in schema-validation mode, uses read-only transactions/connections, and does not expose create/update/delete endpoints. This keeps rollback simple: Django continues to serve its existing read endpoints in parallel while the Spring slice is verified.

Run Django and Spring against the same database with Compose:

```bash
docker compose up -d postgres web spring-careplan-api
```

Django remains on `localhost:8000`; Spring listens on `localhost:8080`. Check Spring health with:

```bash
curl http://localhost:8080/actuator/health
```

Set an existing CarePlan UUID and compare the semantic JSON returned by both implementations:

```bash
CAREPLAN_ID=<existing-careplan-uuid>

curl "http://localhost:8000/api/care-plans/$CAREPLAN_ID/"
curl "http://localhost:8080/api/v1/careplans/$CAREPLAN_ID"

curl "http://localhost:8000/api/care-plans/$CAREPLAN_ID/status/"
curl "http://localhost:8080/api/v1/careplans/$CAREPLAN_ID/status"

curl "http://localhost:8000/api/ops/care-plans/?status=completed&stale_minutes=30"
curl "http://localhost:8080/api/v1/ops/careplans?status=completed&stale_minutes=30"
```

## API

- `POST /api/care-plans/`
- `GET /api/care-plans/<id>/`
- `GET /api/care-plans/<id>/status/`
- `GET /api/care-plans/search/?q=<query>`
- `GET /api/care-plans/<id>/download/`

The Django API contract is documented in [docs/openapi.yaml](docs/openapi.yaml).

Validate the API contract locally:

```bash
python scripts/validate_openapi.py
pytest tests/contract -q
```

`POST /api/care-plans/` stores `status='pending'`, submits work through the configured execution backend, and returns `202 Accepted` immediately.

Celery remains the default backend. Kubernetes is an alternate backend that creates a `CarePlanJob` custom resource and lets a Go controller materialize the child `Job`.

## How to verify Celery is working

Watch worker logs:

```bash
docker compose logs -f worker
```

You should see:

1. `celery@... ready.` when the worker starts
2. After form submit: `Task careplans.generate_care_plan[...] received`
3. Then either `succeeded` / `completed`, or retry lines, or final failure

The UI polls `/api/care-plans/<careplan_id>/status/` until the plan is `completed` or `failed`. You can also open:

`http://127.0.0.1:8000/api/care-plans/<careplan_id>/`

Optional learning command:

```bash
python manage.py process_careplan_queue
```

## Kubernetes

Kubernetes uses a typed `CarePlanJob` custom resource and a Go controller that reconciles one deterministic child `Job`.

Minimal smoke test:

```bash
kind create cluster
kubectl apply -f operator/config/crd/bases/careplan.example.io_careplanjobs.yaml
cd operator
go run ./...
kubectl apply -f config/samples/careplan.example.io_v1alpha1_careplanjob.yaml
kubectl get careplanjobs
kubectl get jobs
kubectl describe careplanjob careplan-00000000000000000000000000000001
```

The key invariant is idempotency: repeated reconciliation of one `CarePlanJob` must still produce only one child `Job`.
