"""Integration tests for patient duplicate detection and error responses."""

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client, override_settings
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from careplans.exceptions import BlockError, ValidationError, WarningException
from careplans.models import Patient
from careplans.services import create_provider_patient_order, resolve_patient
from careplans import views as careplan_views

pytestmark = pytest.mark.integration


@csrf_exempt
def _raise_validation(_request):
    raise ValidationError(detail={"npi": "NPI must be exactly 10 digits"})


@csrf_exempt
def _raise_block(_request):
    raise BlockError("NPI already registered to a different name", code="PROVIDER_NPI_NAME_CONFLICT")


@csrf_exempt
def _raise_warning(_request):
    raise WarningException(
        "Possible patient duplicate; pass confirm=True to continue",
        code="PATIENT_CONFIRM",
        warnings=["MRN matches but name/DOB differ"],
    )


urlpatterns = [
    path("test/validation/", _raise_validation),
    path("test/block/", _raise_block),
    path("test/warning/", _raise_warning),
    path("api/care-plans/", careplan_views.create_care_plan),
    path("api/care-plans/search/", careplan_views.search_care_plans),
    path("api/care-plans/<str:plan_id>/status/", careplan_views.get_care_plan_status),
    path("api/care-plans/<str:plan_id>/download/", careplan_views.download_care_plan),
    path("api/care-plans/<str:plan_id>/", careplan_views.get_care_plan),
    path("", careplan_views.index),
]


@pytest.fixture
def api_client():
    with override_settings(ROOT_URLCONF=__name__):
        yield Client()


@pytest.mark.django_db
def test_patient_duplicate_flow_requires_confirm_then_succeeds(dob):
    first = create_provider_patient_order(
        provider_name="Dr A",
        provider_npi="1234567890",
        patient_first_name="Jane",
        patient_last_name="Doe",
        patient_mrn="MRN001",
        patient_date_of_birth=dob,
        medication_name="Aspirin",
        confirm=False,
    )
    assert first["warnings"] == []
    assert Patient.objects.filter(mrn="MRN001").count() == 1

    with pytest.raises(WarningException) as caught:
        create_provider_patient_order(
            provider_name="Dr A",
            provider_npi="1234567890",
            patient_first_name="Janet",
            patient_last_name="Doe",
            patient_mrn="MRN001",
            patient_date_of_birth=dob,
            medication_name="Lisinopril",
            confirm=False,
        )
    assert caught.value.type == "warning"
    assert caught.value.code == "PATIENT_CONFIRM"

    confirmed = create_provider_patient_order(
        provider_name="Dr A",
        provider_npi="1234567890",
        patient_first_name="Janet",
        patient_last_name="Doe",
        patient_mrn="MRN001",
        patient_date_of_birth=dob,
        medication_name="Lisinopril",
        confirm=True,
    )
    assert confirmed["patient"].id == first["patient"].id
    assert any("MRN matches" in item for item in confirmed["warnings"])
    assert confirmed["order"].medication_name == "Lisinopril"


@pytest.mark.django_db
def test_identity_cross_mrn_warning_then_confirm(dob):
    resolve_patient("Jane", "Doe", "MRN001", dob)

    with pytest.raises(WarningException) as caught:
        create_provider_patient_order(
            provider_name="Dr A",
            provider_npi="1234567890",
            patient_first_name="Jane",
            patient_last_name="Doe",
            patient_mrn="MRN002",
            patient_date_of_birth=dob,
            medication_name="Metformin",
            confirm=False,
        )
    assert any("Name+DOB" in item for item in caught.value.warnings)

    result = create_provider_patient_order(
        provider_name="Dr A",
        provider_npi="1234567890",
        patient_first_name="Jane",
        patient_last_name="Doe",
        patient_mrn="MRN002",
        patient_date_of_birth=dob,
        medication_name="Metformin",
        confirm=True,
    )
    assert result["patient"].mrn == "MRN002"
    assert Patient.objects.filter(mrn__in=["MRN001", "MRN002"]).count() == 2
    assert result["order"].medication_name == "Metformin"

@pytest.mark.django_db
def test_middleware_returns_unified_validation_json(api_client):
    response = api_client.get("/test/validation/")
    assert response.status_code == 400
    body = response.json()
    assert body["type"] == "validation"
    assert body["http_status"] == 400
    assert "npi" in body["detail"]
    assert body["warnings"] == []


@pytest.mark.django_db
def test_middleware_returns_unified_block_json(api_client):
    response = api_client.get("/test/block/")
    assert response.status_code == 409
    body = response.json()
    assert body["type"] == "block"
    assert body["code"] == "PROVIDER_NPI_NAME_CONFLICT"


@pytest.mark.django_db
def test_middleware_returns_unified_warning_json(api_client):
    response = api_client.get("/test/warning/")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "warning"
    assert body["code"] == "PATIENT_CONFIRM"
    assert body["warnings"]


@pytest.mark.django_db
def test_invalid_input_through_orchestrator_maps_to_validation():
    with pytest.raises(ValidationError) as caught:
        create_provider_patient_order(
            provider_name="Dr A",
            provider_npi="12",
            patient_first_name="Jane",
            patient_last_name="Doe",
            patient_mrn="1",
            patient_date_of_birth=date(1990, 1, 1),
            medication_name="Med",
        )
    body = caught.value.to_dict()
    assert body["type"] == "validation"
    assert body["http_status"] == 400
    assert "npi" in body["detail"]
    assert "mrn" in body["detail"]


@pytest.mark.django_db
def test_careplan_api_create_status_search_download(api_client):
    with patch("careplans.services.generate_care_plan_task") as task:
        task.delay = MagicMock()
        create = api_client.post(
            "/api/care-plans/",
            data=json.dumps(
                {
                    "patient_first_name": "Ann",
                    "patient_last_name": "Bee",
                    "patient_mrn": "INT001",
                    "medication_name": "MedA",
                    "additional_diagnosis": "A, B",
                    "medication_history": "X",
                }
            ),
            content_type="application/json",
        )
    assert create.status_code == 202
    plan_id = create.json()["careplan_id"]

    detail = api_client.get(f"/api/care-plans/{plan_id}/")
    assert detail.status_code == 200

    missing = api_client.get("/api/care-plans/00000000-0000-0000-0000-000000000000/")
    assert missing.status_code == 404

    status = api_client.get(f"/api/care-plans/{plan_id}/status/")
    assert status.status_code == 200
    assert set(status.json().keys()) == {"id", "status", "content", "error"}

    bad_method = api_client.post(f"/api/care-plans/{plan_id}/status/")
    assert bad_method.status_code == 405

    search = api_client.get("/api/care-plans/search/?q=INT001")
    assert search.status_code == 200
    assert any(item["id"] == plan_id for item in search.json()["results"])

    from careplans.models import CarePlan

    CarePlan.objects.filter(id=plan_id).update(
        status="completed",
        care_plan={
            "problem_list": ["p"],
            "goals": ["g"],
            "pharmacist_interventions": ["i"],
            "monitoring_plan": ["m"],
        },
    )
    download = api_client.get(f"/api/care-plans/{plan_id}/download/")
    assert download.status_code == 200
    assert b"Problem list:" in download.content

    missing_status = api_client.get("/api/care-plans/00000000-0000-0000-0000-000000000000/status/")
    assert missing_status.status_code == 404

    missing_download = api_client.get("/api/care-plans/00000000-0000-0000-0000-000000000000/download/")
    assert missing_download.status_code == 404

    index = api_client.get("/")
    assert index.status_code == 200


@pytest.mark.django_db
def test_careplan_enqueue_failure_returns_503(api_client):
    with patch("careplans.services.generate_care_plan_task") as task:
        task.delay.side_effect = RuntimeError("down")
        response = api_client.post(
            "/api/care-plans/",
            data=json.dumps({"patient_mrn": "FAIL01"}),
            content_type="application/json",
        )
    assert response.status_code == 503
    assert response.json()["status"] == "failed"
