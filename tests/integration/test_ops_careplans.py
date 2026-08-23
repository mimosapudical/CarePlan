from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import MagicMock, patch

import pytest
from django.db import close_old_connections
from django.test import Client
from django.utils import timezone

from careplans.exceptions import BlockError
from careplans.models import CarePlan
from careplans.services import get_ops_care_plans, retry_failed_care_plan

pytestmark = pytest.mark.integration


@pytest.mark.django_db
def test_failed_job_can_be_retried():
    record = CarePlan.objects.create(
        status=CarePlan.STATUS_FAILED,
        history=[CarePlan.STATUS_PENDING, CarePlan.STATUS_FAILED],
        error="worker unavailable",
    )
    backend = MagicMock()
    with patch("careplans.services.get_execution_backend", return_value=backend):
        response = Client().post(f"/api/ops/care-plans/{record.id}/retry/")
    record.refresh_from_db()
    assert response.status_code == 202
    assert response.json()["status"] == CarePlan.STATUS_PENDING
    assert record.history == ["pending", "failed", "pending"]
    assert record.error is None
    assert record.manual_retry_count == 1
    assert record.last_manual_retry_at is not None
    assert record.queued_at == record.last_manual_retry_at
    backend.submit.assert_called_once_with(str(record.id))


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["pending", "processing", "completed"])
def test_non_failed_job_returns_conflict(status):
    record = CarePlan.objects.create(status=status, history=[status])
    with patch("careplans.services.get_execution_backend") as backend:
        response = Client().post(f"/api/ops/care-plans/{record.id}/retry/")
    assert response.status_code == 409
    backend.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("plan_id", [
    "00000000-0000-0000-0000-000000000000",
    "not-a-uuid",
])
def test_unknown_job_returns_not_found(plan_id):
    assert Client().post(f"/api/ops/care-plans/{plan_id}/retry/").status_code == 404


@pytest.mark.django_db
def test_failed_backend_submission_restores_failed_state():
    record = CarePlan.objects.create(status="failed", history=["failed"], error="first failure")
    backend = MagicMock()
    backend.submit.side_effect = RuntimeError("queue unavailable")
    with patch("careplans.services.get_execution_backend", return_value=backend):
        response = Client().post(f"/api/ops/care-plans/{record.id}/retry/")
    record.refresh_from_db()
    assert response.status_code == 503
    assert record.status == "failed"
    assert record.history == ["failed", "pending", "failed"]
    assert "queue unavailable" in record.error
    assert record.manual_retry_count == 1


@pytest.mark.django_db
def test_double_retry_cannot_enqueue_twice():
    record = CarePlan.objects.create(status="failed", history=["failed"])
    backend = MagicMock()
    with patch("careplans.services.get_execution_backend", return_value=backend):
        first = Client().post(f"/api/ops/care-plans/{record.id}/retry/")
        second = Client().post(f"/api/ops/care-plans/{record.id}/retry/")
    assert first.status_code == 202
    assert second.status_code == 409
    backend.submit.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_concurrent_retry_cannot_enqueue_twice():
    record = CarePlan.objects.create(status="failed", history=["failed"])
    backend = MagicMock()
    barrier = Barrier(2)

    def attempt_retry():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                _, queued = retry_failed_care_plan(record.id)
                return queued
            except BlockError:
                return False
        finally:
            close_old_connections()

    with patch("careplans.services.get_execution_backend", return_value=backend):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: attempt_retry(), range(2)))
    assert sorted(results) == [False, True]
    backend.submit.assert_called_once()
    record.refresh_from_db()
    assert record.manual_retry_count == 1


@pytest.mark.django_db
def test_stale_classification_and_status_filtering():
    stale_pending = CarePlan.objects.create(status="pending")
    stale_processing = CarePlan.objects.create(status="processing")
    old_failed = CarePlan.objects.create(status="failed")
    fresh_pending = CarePlan.objects.create(status="pending")
    old = timezone.now() - timedelta(minutes=45)
    CarePlan.objects.filter(id__in=[stale_pending.id, stale_processing.id, old_failed.id]).update(updated_at=old)
    response = Client().get("/api/ops/care-plans/?stale_minutes=30")
    rows = {item["id"]: item for item in response.json()["results"]}
    assert rows[str(stale_pending.id)]["stale"] is True
    assert rows[str(stale_processing.id)]["stale"] is True
    assert rows[str(old_failed.id)]["stale"] is False
    assert rows[str(fresh_pending.id)]["stale"] is False
    assert all(record.status == "failed" for record in get_ops_care_plans(status="failed"))
    filtered = Client().get("/api/ops/care-plans/?status=failed")
    assert [item["id"] for item in filtered.json()["results"]] == [str(old_failed.id)]


@pytest.mark.django_db
def test_ops_api_does_not_expose_patient_information():
    record = CarePlan.objects.create(
        status="failed",
        payload={"patient_mrn": "SECRET-MRN", "patient_first_name": "SecretPatient"},
        care_plan={"notes": "SECRET-PLAN"},
    )
    response = Client().get("/api/ops/care-plans/")
    body = response.json()
    assert response.status_code == 200
    assert body["results"][0]["id"] == str(record.id)
    assert set(body["results"][0]) == {
        "id", "status", "error", "queued_at", "created_at", "updated_at",
        "manual_retry_count", "last_manual_retry_at", "stale",
    }
    assert b"SECRET-MRN" not in response.content
    assert b"SecretPatient" not in response.content
    assert b"SECRET-PLAN" not in response.content


@pytest.mark.django_db
def test_ops_api_rejects_invalid_filters_and_methods():
    client = Client()
    assert client.get("/api/ops/care-plans/?status=unknown").status_code == 400
    assert client.get("/api/ops/care-plans/?stale_minutes=0").status_code == 400
    assert client.get("/api/ops/care-plans/?stale_minutes=oops").status_code == 400
    assert client.post("/api/ops/care-plans/").status_code == 405
    assert client.get("/api/ops/care-plans/not-a-uuid/retry/").status_code == 405
