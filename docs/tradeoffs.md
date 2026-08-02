# Engineering tradeoffs

Decisions that shaped CarePlan’s current shape, and what we would change next.

## Why asynchronous processing

Care-plan generation calls an LLM and can take seconds to tens of seconds. Doing that on the request thread would:

- Block HTTP workers and amplify tail latency under load
- Force clients to hold long connections open
- Make retries harder without duplicating user-facing timeouts

Accept → enqueue → process → poll (or fetch by id) keeps the write path fast and isolates failure/retry in the worker.

## Why Celery + Redis locally

Local and Docker need a durable-enough queue without standing up AWS.

| Choice | Rationale |
|--------|-----------|
| Celery | Familiar Python worker model; retries and backoff map cleanly to generation failures |
| Redis | Lightweight broker for Compose; enough for a single-dev / MVP worker |

This mirrors the cloud pattern (queue + worker) without requiring SQS during day-to-day development.

## Why Terraform / Infrastructure as Code

Manual console setup does not reproduce:

- Who created which resource, with which IAM and triggers
- Repeatable apply/destroy for practice accounts
- Reviewable diffs when wiring changes (API Gateway ↔ Lambda ↔ SQS ↔ RDS)

Terraform under `infra/practice/` encodes those relationships so the team can recreate or tear down the stack from git. IaC is the source of truth for cloud topology; the console is for inspection, not for primary provisioning.

## Current limitations

- AWS Lambdas in the practice module may still use **stub handlers**; full Django packaging on Lambda is incomplete.
- Practice RDS is oriented toward learning (e.g. public access options); **not** production hardening (private subnets, least-privilege SG, Secrets Manager, etc.).
- Local Django HTTP API and AWS HTTP API paths are **parallel surfaces**, not yet a single deployed artifact.
- Terraform state is **local** to the practice folder — no remote backend / locking for a multi-engineer team.
- Cloud stack is **ephemeral by policy**; there is no long-lived shared staging environment in-repo.

## Future improvements

- Package real handlers (or container images) for Lambda and share `careplans/` domain code end to end on AWS
- Put Lambdas in a VPC; lock RDS to Lambda security groups; store DB credentials in Secrets Manager
- Remote Terraform state (S3 + DynamoDB lock) and environment separation (dev/stage)
- Unify API contracts between Django and API Gateway where it makes sense
- Observability on the cloud path (structured logs, metrics, alarms) beyond local Prometheus profile

## Related docs

- [architecture.md](architecture.md)
- [deployment.md](deployment.md)
- [engineering-notes/day15.md](engineering-notes/day15.md)
