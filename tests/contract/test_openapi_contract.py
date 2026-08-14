import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from django.test import Client, override_settings
from django.urls import path
from openapi_spec_validator import validate

from careplans import views as careplan_views
from careplans.models import CarePlan


urlpatterns = [
    path("api/care-plans/", careplan_views.create_care_plan),
    path("api/care-plans/search/", careplan_views.search_care_plans),
    path("api/care-plans/<str:plan_id>/status/", careplan_views.get_care_plan_status),
    path("api/care-plans/<str:plan_id>/download/", careplan_views.download_care_plan),
    path("api/care-plans/<str:plan_id>/", careplan_views.get_care_plan),
]


@pytest.fixture
def openapi_document():
    path = Path(__file__).resolve().parents[2] / "docs" / "openapi.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture
def api_client():
    with override_settings(ROOT_URLCONF=__name__):
        yield Client()


def _schema_property_keys(document, schema_name):
    return set(document["components"]["schemas"][schema_name]["properties"].keys())


def test_openapi_document_is_valid(openapi_document):
    validate(openapi_document)


def test_expected_public_api_paths_exist(openapi_document):
    expected_paths = {
        "/api/care-plans/",
        "/api/care-plans/search/",
        "/api/care-plans/{plan_id}/status/",
        "/api/care-plans/{plan_id}/download/",
        "/api/care-plans/{plan_id}/",
    }

    assert set(openapi_document["paths"].keys()) == expected_paths


def test_status_enum_matches_django_model(openapi_document):
    model_statuses = {value for value, _label in CarePlan.STATUS_CHOICES}
    contract_statuses = set(openapi_document["components"]["schemas"]["CarePlanStatus"]["enum"])

    assert contract_statuses == model_statuses


@pytest.mark.django_db
def test_live_status_response_matches_documented_fields(api_client, openapi_document):
    record = CarePlan.objects.create(payload={"patient_mrn": "CTR001"})

    response = api_client.get(f"/api/care-plans/{record.id}/status/")

    assert response.status_code == 200
    assert set(response.json().keys()) == _schema_property_keys(openapi_document, "CarePlanStatusResponse")


@pytest.mark.django_db
def test_live_detail_response_matches_documented_fields(api_client, openapi_document):
    record = CarePlan.objects.create(payload={"patient_mrn": "CTR002"})

    response = api_client.get(f"/api/care-plans/{record.id}/")

    assert response.status_code == 200
    assert set(response.json().keys()) == _schema_property_keys(openapi_document, "CarePlanDetail")


@pytest.mark.django_db
def test_create_response_matches_documented_fields(api_client, openapi_document):
    backend = MagicMock()
    with patch("careplans.services.get_execution_backend", return_value=backend):
        response = api_client.post(
            "/api/care-plans/",
            data=json.dumps({"patient_mrn": "CTR003"}),
            content_type="application/json",
        )

    assert response.status_code == 202
    assert set(response.json().keys()) == _schema_property_keys(openapi_document, "CarePlanAcceptedResponse")


@pytest.mark.django_db
def test_download_content_type_matches_contract(api_client, openapi_document):
    record = CarePlan.objects.create(
        status=CarePlan.STATUS_COMPLETED,
        payload={"patient_mrn": "CTR004"},
        care_plan={
            "problem_list": ["p"],
            "goals": ["g"],
            "pharmacist_interventions": ["i"],
            "monitoring_plan": ["m"],
        },
    )

    response = api_client.get(f"/api/care-plans/{record.id}/download/")
    documented_media_types = set(
        openapi_document["paths"]["/api/care-plans/{plan_id}/download/"]["get"]["responses"]["200"]["content"].keys()
    )

    assert response.status_code == 200
    assert documented_media_types == {"text/plain"}
    assert response["Content-Type"].startswith("text/plain")
