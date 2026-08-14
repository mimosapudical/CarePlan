# Engineering tradeoffs

Decisions that shaped CarePlan's current shape, and what we would change next.

## Why asynchronous processing

Care-plan generation calls an LLM and can take seconds to tens of seconds. Doing that on the request thread would:

- Block HTTP workers and amplify tail latency under load
- Force clients to hold long connections open
- Make retries harder without duplicating user-facing timeouts

Accept -> enqueue -> process -> poll (or fetch by id) keeps the write path fast and isolates failure/retry in the worker.

## Why introduce an execution boundary

The business service previously called Celery `.delay()` directly even though runtime execution is an infrastructure concern. A tiny `ExecutionBackend` boundary lets the same service submit work to Celery or Kubernetes without knowing the runtime mechanism.

## Why keep Celery

Celery is still the simplest path for local and small deployments, and the existing application already supports it well.

## Why Kubernetes

For Kubernetes-hosted environments, a controller provides workload lifecycle through desired-state reconciliation. The custom resource expresses intent; the controller materializes the child `Job`.

## Why not say Kubernetes is better

Celery, AWS, and Kubernetes solve different operational problems. The right choice depends on the runtime you are already running.

## Why CarePlanJob references a database ID

The medical/application payload stays in PostgreSQL rather than being duplicated into Kubernetes metadata. The CR only needs the work identifier and runtime metadata.

## Why the Go controller does not generate care plans

Runtime orchestration stays separate from Python domain behavior. Python owns the generation logic; Go owns resource reconciliation.

## Why deterministic Job names

Reconciliation is repeated. Deterministic identity lets the controller check for an existing child `Job` and remain idempotent.

## Why owner references

Owner references express resource ownership and let Kubernetes garbage collection remove the child `Job` when the `CarePlanJob` is deleted.

## Why Kubernetes Job owns retries

Avoid nested retries between the controller, the `Job`, and application code. Celery retains its own retry semantics; Kubernetes uses `backoffLimit`.

## Current limitations

- AWS Lambdas in the practice module may still use stub handlers; full Django packaging on Lambda is incomplete.
- Practice RDS is oriented toward learning, not production hardening.
- The Django HTTP API now has an explicit OpenAPI contract guarded by CI, while AWS API Gateway remains a parallel surface rather than a single unified deployed API artifact.
- Terraform state is local to the practice folder.
- Cloud stack is ephemeral by policy.

## Future improvements

- Package real handlers or container images for Lambda and share `careplans/` domain code end to end on AWS
- Put Lambdas in a VPC; lock RDS to Lambda security groups; store DB credentials in Secrets Manager
- Remote Terraform state and environment separation
- Unify Django and AWS API Gateway contracts where it makes sense; the Django contract is explicit and CI-protected, but cross-runtime contract unification remains future work
- Observability on the cloud path beyond local logging
