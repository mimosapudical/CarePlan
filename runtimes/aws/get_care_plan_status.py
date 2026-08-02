"""
AWS Lambda: GET care plan status (+ content when completed).

Fits the shared-runtime layout:

  API Gateway
      → runtimes/aws/get_care_plan_status.py   ← THIS FILE (transport only)
          → careplans.services.get_care_plan    ← shared DB logic
          → careplans.serializers.status_to_dict ← shared response shape

Local equivalent: Django view get_care_plan_status in careplans/views.py

API Gateway (HTTP API or REST proxy) example:
  GET /api/care-plans/{plan_id}/status/

Environment (Lambda):
  DJANGO_SETTINGS_MODULE=careplan_mvp.settings
  POSTGRES_HOST / POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_PORT
  (and any other settings your .env already uses)
"""

from __future__ import annotations

import json
import os
from typing import Any


def _ensure_django() -> None:
    """Initialize Django once per Lambda container (cold start)."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "careplan_mvp.settings")

    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """API Gateway proxy integration response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def _plan_id_from_event(event: dict[str, Any]) -> str | None:
    """Support HTTP API v2, REST API, and direct invoke test events."""
    path_params = event.get("pathParameters") or {}
    if path_params.get("plan_id"):
        return str(path_params["plan_id"])
    if path_params.get("id"):
        return str(path_params["id"])

    # Direct test: { "plan_id": "..." }
    if event.get("plan_id"):
        return str(event["plan_id"])

    # Fallback: last non-empty path segment before optional "status"
    # e.g. /api/care-plans/<uuid>/status/
    raw_path = event.get("rawPath") or event.get("path") or ""
    parts = [p for p in raw_path.strip("/").split("/") if p]
    if parts and parts[-1] == "status" and len(parts) >= 2:
        return parts[-2]
    if parts:
        return parts[-1]
    return None


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda entrypoint.

    Reuses:
      - services.get_care_plan(plan_id)
      - serializers.status_to_dict(record)
        → { id, status, content, error }  (content only when completed)
    """
    _ensure_django()

    # Import AFTER django.setup() so ORM/apps are ready.
    from careplans import serializers, services

    method = (
        (event.get("requestContext") or {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "GET"
    ).upper()
    if method not in {"GET", "HEAD"}:
        return _response(405, {"error": "method not allowed"})

    plan_id = _plan_id_from_event(event)
    if not plan_id:
        return _response(400, {"error": "plan_id is required"})

    record = services.get_care_plan(plan_id)
    if record is None:
        return _response(404, {"error": "not found"})

    return _response(200, serializers.status_to_dict(record))
