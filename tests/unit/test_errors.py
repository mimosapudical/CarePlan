"""Unit tests ensuring bad input maps to the correct app errors."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.exceptions import ValidationError as DRFValidationError

from careplans.exception_handler import (
    AppExceptionMiddleware,
    exception_handler,
    render_app_exception,
)
from careplans.exceptions import (
    BaseAppException,
    BlockError,
    ValidationError,
    WarningException,
)
from careplans.models import Order, Patient
from careplans.serializers import validate_provider_patient_fields
from careplans.services import (
    create_care_plan,
    create_order,
    create_provider_patient_order,
    get_care_plan,
    resolve_provider,
    search_care_plans,
)

pytestmark = pytest.mark.unit


def test_validation_error_shape():
    exc = ValidationError(
        message="Validation failed",
        code="VALIDATION_ERROR",
        detail={"npi": "NPI must be exactly 10 digits"},
    )
    body = exc.to_dict()

    assert body["type"] == "validation"
    assert body["http_status"] == 400
    assert body["code"] == "VALIDATION_ERROR"
    assert body["detail"]["npi"]
    assert body["warnings"] == []


def test_block_error_shape():
    exc = BlockError("blocked", code="PROVIDER_NPI_NAME_CONFLICT")
    body = exc.to_dict()

    assert body["type"] == "block"
    assert body["http_status"] == 409


def test_warning_exception_shape():
    exc = WarningException(
        "confirm",
        code="PATIENT_CONFIRM",
        warnings=["MRN matches but name/DOB differ"],
    )
    body = exc.to_dict()

    assert body["type"] == "warning"
    assert body["http_status"] == 200
    assert body["warnings"] == ["MRN matches but name/DOB differ"]


def test_invalid_npi_raises_validation_error():
    with pytest.raises(ValidationError) as caught:
        validate_provider_patient_fields(npi="123", mrn="MRN001")

    assert caught.value.type == "validation"
    assert caught.value.http_status == 400
    assert "npi" in caught.value.detail


def test_invalid_mrn_raises_validation_error():
    with pytest.raises(ValidationError) as caught:
        validate_provider_patient_fields(npi="1234567890", mrn="1")

    assert "mrn" in caught.value.detail


def test_invalid_npi_and_mrn_both_in_detail():
    with pytest.raises(ValidationError) as caught:
        validate_provider_patient_fields(npi="abc", mrn="xx")

    assert "npi" in caught.value.detail
    assert "mrn" in caught.value.detail


def test_non_string_npi_and_mrn_invalid():
    with pytest.raises(ValidationError) as caught:
        validate_provider_patient_fields(npi=1234567890, mrn=123456)

    assert "npi" in caught.value.detail
    assert "mrn" in caught.value.detail


def test_valid_npi_and_mrn_pass():
    validate_provider_patient_fields(npi="1234567890", mrn="MRN001")


@pytest.mark.django_db
def test_provider_npi_conflict_is_block_error():
    resolve_provider("Dr A", "1234567890")

    with pytest.raises(BlockError) as caught:
        resolve_provider("Dr B", "1234567890")

    assert caught.value.type == "block"
    assert caught.value.code == "PROVIDER_NPI_NAME_CONFLICT"
    assert caught.value.http_status == 409


@pytest.mark.django_db
def test_provider_reuse_same_name():
    first = resolve_provider("Dr A", "1234567890")
    second = resolve_provider("Dr A", "1234567890")
    assert first.id == second.id


@pytest.mark.django_db
def test_create_provider_patient_order_validation_error():
    with pytest.raises(ValidationError) as caught:
        create_provider_patient_order(
            provider_name="Dr A",
            provider_npi="bad",
            patient_first_name="Jane",
            patient_last_name="Doe",
            patient_mrn="MRN001",
            patient_date_of_birth=date(1990, 1, 1),
            medication_name="Lisinopril",
        )

    assert caught.value.type == "validation"
    assert caught.value.http_status == 400


@pytest.mark.django_db
def test_patient_warning_without_confirm_is_warning_exception(dob):
    create_provider_patient_order(
        provider_name="Dr A",
        provider_npi="1234567890",
        patient_first_name="Jane",
        patient_last_name="Doe",
        patient_mrn="MRN001",
        patient_date_of_birth=dob,
        medication_name="Aspirin",
        confirm=False,
    )

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
    assert caught.value.http_status == 200
    assert caught.value.warnings


@pytest.mark.django_db
def test_same_day_order_is_block_error(dob):
    patient = Patient.objects.create(
        first_name="Jane",
        last_name="Doe",
        mrn="MRN001",
        date_of_birth=dob,
    )
    create_order(patient, "Lisinopril", confirm=False)

    with pytest.raises(BlockError) as caught:
        create_order(patient, "Lisinopril", confirm=False)

    assert caught.value.code == "ORDER_SAME_DAY_DUPLICATE"
    assert caught.value.http_status == 409


@pytest.mark.django_db
def test_cross_day_order_without_confirm_is_warning(dob):
    patient = Patient.objects.create(
        first_name="Jane",
        last_name="Doe",
        mrn="MRN001",
        date_of_birth=dob,
    )
    order, _ = create_order(patient, "Lisinopril", confirm=False)
    Order.objects.filter(id=order.id).update(created_at=timezone.now() - timedelta(days=2))

    with pytest.raises(WarningException) as caught:
        create_order(patient, "Lisinopril", confirm=False)

    assert caught.value.code == "ORDER_CROSS_DAY_CONFIRM"
    assert caught.value.http_status == 200


@pytest.mark.django_db
def test_cross_day_order_with_confirm_succeeds(dob):
    patient = Patient.objects.create(
        first_name="Jane",
        last_name="Doe",
        mrn="MRN001",
        date_of_birth=dob,
    )
    order, _ = create_order(patient, "Lisinopril", confirm=False)
    Order.objects.filter(id=order.id).update(created_at=timezone.now() - timedelta(days=2))

    new_order, warnings = create_order(patient, "Lisinopril", confirm=True)
    assert new_order.id != order.id
    assert any("different day" in item for item in warnings)


def test_middleware_renders_block_error():
    response = AppExceptionMiddleware(lambda r: None).process_exception(
        None, BlockError("blocked", code="B")
    )
    assert isinstance(response, JsonResponse)
    assert response.status_code == 409


def test_middleware_ignores_unknown_exception():
    response = AppExceptionMiddleware(lambda r: None).process_exception(None, ValueError("x"))
    assert response is None


def test_render_warning_exception_http_200():
    response = render_app_exception(
        WarningException("confirm", code="W", warnings=["dup"])
    )
    assert response.status_code == 200


def test_drf_handler_bridges_drf_validation_error():
    response = exception_handler(DRFValidationError({"npi": ["bad"]}), {})
    assert response.status_code == 400
    assert response.data["type"] == "validation"
    assert response.data["detail"]["npi"] == ["bad"]


def test_drf_handler_bridges_nested_and_list_detail():
    response = exception_handler(
        DRFValidationError({"nested": {"field": ["bad"]}, "list": ["a", "b"]}),
        {},
    )
    assert response.status_code == 400
    assert response.data["type"] == "validation"


def test_drf_handler_passes_through_unknown():
    assert exception_handler(RuntimeError("boom"), {}) is None


def test_drf_handler_base_app_exception():
    response = exception_handler(ValidationError(detail={"mrn": "bad"}), {})
    assert response.status_code == 400
    assert response.data["type"] == "validation"


@pytest.mark.django_db
def test_create_care_plan_enqueue_success():
    with patch("careplans.services.generate_care_plan_task") as task:
        task.delay = MagicMock()
        record, queued = create_care_plan({"patient_mrn": "X", "medication_name": "M"})
        assert queued is True
        assert record.status == "pending"
        task.delay.assert_called_once()


@pytest.mark.django_db
def test_create_care_plan_enqueue_failure():
    with patch("careplans.services.generate_care_plan_task") as task:
        task.delay.side_effect = RuntimeError("broker down")
        record, queued = create_care_plan({"patient_mrn": "Y"})
        assert queued is False
        assert record.status == "failed"
        assert "broker down" in record.error


@pytest.mark.django_db
def test_get_and_search_care_plans():
    with patch("careplans.services.generate_care_plan_task") as task:
        task.delay = MagicMock()
        record, _ = create_care_plan(
            {
                "patient_first_name": "Ann",
                "patient_last_name": "Bee",
                "patient_mrn": "SEARCH",
                "medication_name": "MedA",
            }
        )

    assert get_care_plan(str(record.id)).id == record.id
    assert get_care_plan("00000000-0000-0000-0000-000000000000") is None
    assert get_care_plan("not-a-uuid") is None

    found = search_care_plans("search")
    assert any(item.id == record.id for item in found)
    assert search_care_plans("zzzz-no-match") == []
