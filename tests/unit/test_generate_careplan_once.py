from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from careplans.models import CarePlan

pytestmark = pytest.mark.unit


@pytest.mark.django_db
def test_generate_careplan_once_success():
    record = CarePlan.objects.create(
        status=CarePlan.STATUS_PENDING,
        history=[CarePlan.STATUS_PENDING],
        payload={"patient_mrn": "CMD001", "medication_name": "MedA"},
    )

    with patch(
        "careplans.generation_service.generate_care_plan",
        return_value={
            "problem_list": ["p"],
            "goals": ["g"],
            "pharmacist_interventions": ["i"],
            "monitoring_plan": ["m"],
        },
    ):
        call_command("generate_careplan_once", str(record.id))

    record.refresh_from_db()
    assert record.status == CarePlan.STATUS_COMPLETED
    assert record.care_plan["goals"] == ["g"]


@pytest.mark.django_db
def test_generate_careplan_once_failure_propagates():
    record = CarePlan.objects.create(
        status=CarePlan.STATUS_PENDING,
        history=[CarePlan.STATUS_PENDING],
        payload={"patient_mrn": "CMD002", "medication_name": "MedB"},
    )

    with patch("careplans.generation_service.generate_care_plan", side_effect=RuntimeError("boom")):
        with pytest.raises(CommandError):
            call_command("generate_careplan_once", str(record.id))

    record.refresh_from_db()
    assert record.status == CarePlan.STATUS_PROCESSING
    assert record.error == "boom"

