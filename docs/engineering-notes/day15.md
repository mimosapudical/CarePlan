# Day 15 — Terraform and treating infra as code

Personal notes after wiring the CarePlan practice stack on AWS.

## What was learned

- Cloud pieces that “exist” in the console are not a system until relationships are explicit: who may send to SQS, what triggers generate, who may invoke Lambda from API Gateway, which env vars point at RDS.
- Terraform’s value showed up less in creating a queue and more in encoding those edges so `plan`/`apply`/`destroy` are repeatable.
- HTTP API (API Gateway v2) is a small surface for Lambda proxy integrations: integration → route → `lambda:InvokeFunction` permission.
- PowerShell’s `curl` is not curl; smoke tests need `curl.exe` or `Invoke-RestMethod`, and a real `terraform output` URL — not a placeholder host.

## Why Terraform matters

Manual clicks do not survive a wiped account, a teammate’s laptop, or a week of forgotten SG rules. For a backend team, infra drift is a bug class. Keeping `infra/practice/` in the repo means the topology is reviewable next to application changes, even while handlers are still stubs.

Destroy-after-test is part of the same discipline: practice stacks should be cheap to recreate and expensive to leave running (especially RDS).

## Problems encountered

- Provider blocks duplicated across `.tf` files (`required_providers`) — Terraform wants a single declaration; merged into `main.tf`.
- State lock / stuck processes when apply overlapped — local state is fragile; a remote backend would be the next ops step for shared work.
- Console vs Terraform mental model: a resource “created” in one tool and edited in another becomes undiagnosable; stick to one source of truth.
- Connecting Lambda to RDS is not an IAM checkbox alone — network path (public practice vs VPC) and credentials (env vs secrets) both matter; practice defaults are intentionally loose and must not be copied to production.

## Engineering decisions

- **One practice module** for SQS, RDS, Lambdas, API Gateway, and wiring — easier to destroy as a unit while learning.
- **Shared Lambda role** for practice speed; production would split send vs consume permissions.
- **SQS for cloud async**, Celery + Redis locally — same product shape, different brokers by environment.
- **Stubs first, wiring second** — prove IAM, event source mapping, and routes before investing in Lambda packaging of Django.
- **Ephemeral cloud** — apply to learn, destroy to avoid cost; docs call that out so nobody treats the practice account as staging.

## Future work

- Real Lambda packages (or images) reusing `careplans/` domain code
- VPC + tightened security groups; Secrets Manager for DB password
- Remote state and locking
- Align Django and API Gateway contracts where we keep both

## Related

- [../architecture.md](../architecture.md)
- [../deployment.md](../deployment.md)
- [../tradeoffs.md](../tradeoffs.md)
- [../releases/v0.7.md](../releases/v0.7.md)
