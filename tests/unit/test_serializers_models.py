"""Unit coverage for serializers and models used by patient/order flows."""

from datetime import date
from unittest.mock import MagicMock

import pytest
from django.test import RequestFactory

from careplans.models import CarePlan, Order, Patient, Provider
from careplans.serializers import (
    normalize_payload,
    parse_payload,
    record_to_dict,
    render_care_plan_text,
    status_to_dict,
)

pytestmark = pytest.mark.unit


def test_parse_payload_from_json_body():
    request = RequestFactory().post(
        "/api/care-plans/",
        data='{"patient_mrn": "MRN001"}',
        content_type="application/json",
    )
    assert parse_payload(request)["patient_mrn"] == "MRN001"


def test_parse_payload_from_post_form():
    request = MagicMock()
    request.body = b""
    request.POST.dict.return_value = {"patient_mrn": "MRN001"}
    assert parse_payload(request)["patient_mrn"] == "MRN001"


def test_normalize_payload_splits_comma_lists():
    normalized = normalize_payload(
        {
            "patient_first_name": "Jane",
            "additional_diagnosis": "A, B",
            "medication_history": "X, Y",
        }
    )
    assert normalized["additional_diagnosis"] == ["A", "B"]
    assert normalized["medication_history"] == ["X", "Y"]


def test_normalize_payload_keeps_lists():
    normalized = normalize_payload(
        {
            "additional_diagnosis": ["A"],
            "medication_history": ["X"],
        }
    )
    assert normalized["additional_diagnosis"] == ["A"]
    assert normalized["medication_history"] == ["X"]


@pytest.mark.django_db
def test_record_and_status_serializers():
    record = CarePlan.objects.create(
        status=CarePlan.STATUS_COMPLETED,
        history=["pending", "completed"],
        payload={"patient_first_name": "Jane", "patient_last_name": "Doe", "patient_mrn": "MRN001"},
        care_plan={
            "problem_list": ["p"],
            "goals": ["g"],
            "pharmacist_interventions": ["i"],
            "monitoring_plan": ["m"],
        },
        queued_at=None,
    )
    data = record_to_dict(record)
    assert data["care_plan"]["problem_list"] == ["p"]
    assert data["status"] == "completed"

    pending = CarePlan.objects.create(status=CarePlan.STATUS_PENDING, payload={})
    assert record_to_dict(pending)["care_plan"] is None

    status = status_to_dict(record)
    assert status["content"]["goals"] == ["g"]
    assert status["error"] is None

    failed = CarePlan.objects.create(status=CarePlan.STATUS_FAILED, payload={}, error="boom")
    failed_status = status_to_dict(failed)
    assert failed_status["content"] is None
    assert failed_status["error"] == "boom"

    text = render_care_plan_text(record)
    assert "Problem list:" in text
    assert "- p" in text


@pytest.mark.django_db
def test_project_urls_importable():
    from careplans import urls as careplan_urls

    assert any(getattr(pattern, "name", None) == "create_care_plan" for pattern in careplan_urls.urlpatterns)


@pytest.mark.django_db
def test_model_str_methods(dob):
    provider = Provider.objects.create(name="Dr A", npi="1234567890")
    patient = Patient.objects.create(
        first_name="Jane",
        last_name="Doe",
        mrn="MRN001",
        date_of_birth=dob,
    )
    order = Order.objects.create(patient=patient, medication_name="Lisinopril")
    assert "Dr A" in str(provider)
    assert "MRN001" in str(patient)
    assert "Lisinopril" in str(order)
