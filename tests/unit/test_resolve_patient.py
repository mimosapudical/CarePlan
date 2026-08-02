"""Unit tests for Patient duplicate detection (resolve_patient)."""

from datetime import date

import pytest

from careplans.models import Patient
from careplans.services import resolve_patient

pytestmark = pytest.mark.unit


@pytest.mark.django_db
def test_create_new_patient_when_no_match(dob):
    patient, warnings = resolve_patient("Jane", "Doe", "MRN001", dob)

    assert patient.mrn == "MRN001"
    assert patient.first_name == "Jane"
    assert patient.last_name == "Doe"
    assert patient.date_of_birth == dob
    assert warnings == []
    assert Patient.objects.filter(mrn="MRN001").count() == 1


@pytest.mark.django_db
def test_reuse_when_mrn_name_and_dob_match(dob):
    original, _ = resolve_patient("Jane", "Doe", "MRN001", dob)

    reused, warnings = resolve_patient("Jane", "Doe", "MRN001", dob)

    assert reused.id == original.id
    assert warnings == []
    assert Patient.objects.count() == 1


@pytest.mark.django_db
def test_warn_when_mrn_matches_but_first_name_differs(dob):
    original, _ = resolve_patient("Jane", "Doe", "MRN001", dob)

    reused, warnings = resolve_patient("Janet", "Doe", "MRN001", dob)

    assert reused.id == original.id
    assert "MRN matches but name/DOB differ" in warnings
    assert Patient.objects.count() == 1


@pytest.mark.django_db
def test_warn_when_mrn_matches_but_last_name_differs(dob):
    original, _ = resolve_patient("Jane", "Doe", "MRN001", dob)

    reused, warnings = resolve_patient("Jane", "Smith", "MRN001", dob)

    assert reused.id == original.id
    assert "MRN matches but name/DOB differ" in warnings


@pytest.mark.django_db
def test_warn_when_mrn_matches_but_dob_differs(dob):
    original, _ = resolve_patient("Jane", "Doe", "MRN001", dob)

    reused, warnings = resolve_patient("Jane", "Doe", "MRN001", date(1991, 2, 20))

    assert reused.id == original.id
    assert "MRN matches but name/DOB differ" in warnings


@pytest.mark.django_db
def test_warn_when_name_and_dob_match_but_mrn_differs(dob):
    first, _ = resolve_patient("Jane", "Doe", "MRN001", dob)

    second, warnings = resolve_patient("Jane", "Doe", "MRN002", dob)

    assert second.id != first.id
    assert second.mrn == "MRN002"
    assert "Name+DOB match another patient with different MRN" in warnings
    assert Patient.objects.count() == 2


@pytest.mark.django_db
def test_no_identity_warning_when_only_name_matches(dob):
    resolve_patient("Jane", "Doe", "MRN001", dob)

    other, warnings = resolve_patient("Jane", "Doe", "MRN003", date(1985, 5, 5))

    assert other.mrn == "MRN003"
    assert warnings == []
