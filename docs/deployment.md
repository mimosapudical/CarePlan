# Deployment

Two supported ways to run CarePlan: local Docker Compose, and a short-lived AWS practice stack via Terraform.

## Prerequisites

| Environment | Needs |
|-------------|--------|
| Local / Docker | Docker Desktop (or Compose), optional Python 3.x for non-Docker runs |
| Next.js product UI | Node.js 22 and npm |
| LLM (Gemini / Vertex) | GCP project, ADC via `gcloud auth application-default login`, `.env` with `GCP_PROJECT` / `GCP_LOCATION` |
| AWS practice | AWS CLI credentials, [Terraform](https://www.terraform.io/) ≥ 1.5, password for RDS |

## Local: Docker Compose

From the repository root:

```bash
docker compose up --build
```

Services:

| Service | Role | Host ports |
|---------|------|------------|
| `web` | Django | `8000` |
| `worker` | Celery | — |
| `postgres` | Database | `5432` |
| `redis` | Celery broker | `6379` |

Open `http://127.0.0.1:8000/`.

The same Compose command also starts the `frontend` service. Open `http://127.0.0.1:3000/` for the Next.js product interface. Inside Compose, `DJANGO_API_BASE_URL` is `http://web:8000`.

### Product UI without Docker

Start Django on port 8000, then run:

```bash
cd web
cp .env.example .env.local
npm ci
npm run dev
```

The UI runs at `http://127.0.0.1:3000/`. Its server-only `DJANGO_API_BASE_URL` defaults to `http://127.0.0.1:8000`; it is not exposed to browser JavaScript.

Optional monitoring profile (Prometheus / Grafana) is documented in Compose; enable only when needed.

### Local without Docker

See the **Local Run** section in [README.md](../README.md): install `requirements.txt`, set `POSTGRES_*`, migrate, runserver, and start a Celery worker in a second terminal. PostgreSQL and Redis must already be available.

### Tear down (local)

```bash
docker compose down
```

Add `-v` only if you intend to wipe local database volumes.

## Cloud: Terraform practice stack

Infrastructure lives in `infra/practice/` (API Gateway, three Lambdas, SQS + DLQ, RDS). This is a **learning / validation** stack, not a production account layout.

### Apply

```powershell
cd infra/practice
$env:TF_VAR_db_password = "YourStrongPassword1"
terraform init   # first time only
terraform plan
terraform apply
```

Useful outputs after apply:

- `api_gateway_endpoint` / `api_post_orders_url`
- `queue_url`, `rds_endpoint`
- Lambda function names

Example smoke calls (PowerShell: use `curl.exe`, not the `curl` alias):

```powershell
curl.exe -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/orders
curl.exe https://<api-id>.execute-api.us-east-1.amazonaws.com/orders/123
```

### Destroy (required after testing)

```powershell
cd infra/practice
$env:TF_VAR_db_password = "YourStrongPassword1"
terraform destroy
```

Cloud resources are created only for testing and **destroyed afterward** to minimize AWS cost. Leaving RDS and related resources running will incur charges.

### Notes

- Terraform state under `infra/practice/` is local and gitignored; do not commit `*.tfstate`.
- Lambda packages in this practice module currently use stub handlers under `runtimes/aws/stubs/`; wiring (IAM, event source, routes, env vars) is what Terraform validates end to end.
- RDS password is supplied only via `TF_VAR_db_password` — never commit secrets.

## CI

Pull requests run tests via GitHub Actions (see `.github/workflows/`). CI does **not** apply Terraform or create AWS resources.

## Related docs

- [architecture.md](architecture.md)
- [tradeoffs.md](tradeoffs.md)
- [releases/v0.7.md](releases/v0.7.md)
