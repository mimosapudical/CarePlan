import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from .debug_trace import debug_break
from .exceptions import BlockError, WarningException
from .execution import get_execution_backend
from .models import CarePlan, Order, Patient, Provider

logger = logging.getLogger(__name__)


def resolve_provider(name, npi):
    existing = Provider.objects.filter(npi=npi).first()
    if existing:
        if existing.name == name:
            return existing
        raise BlockError(
            "NPI already registered to a different name",
            code="PROVIDER_NPI_NAME_CONFLICT",
            detail={"npi": npi, "existing_name": existing.name, "incoming_name": name},
        )
    return Provider.objects.create(name=name, npi=npi)


def resolve_patient(first_name, last_name, mrn, date_of_birth):
    warnings = []
    by_mrn = Patient.objects.filter(mrn=mrn).first()
    if by_mrn:
        if (
            by_mrn.first_name != first_name
            or by_mrn.last_name != last_name
            or by_mrn.date_of_birth != date_of_birth
        ):
            warnings.append("MRN matches but name/DOB differ")
        return by_mrn, warnings

    by_identity = (
        Patient.objects.filter(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
        )
        .exclude(mrn=mrn)
        .first()
    )
    if by_identity:
        warnings.append("Name+DOB match another patient with different MRN")

    patient = Patient.objects.create(
        first_name=first_name,
        last_name=last_name,
        mrn=mrn,
        date_of_birth=date_of_birth,
    )
    return patient, warnings


def create_order(patient, medication_name, *, confirm=False):
    today = timezone.localdate()
    same_med = Order.objects.filter(patient=patient, medication_name=medication_name)

    if same_med.filter(created_at__date=today).exists():
        raise BlockError(
            "Duplicate order: same patient + medication + day",
            code="ORDER_SAME_DAY_DUPLICATE",
            detail={
                "patient_id": patient.id,
                "medication_name": medication_name,
                "date": str(today),
            },
        )

    prior_exists = same_med.exclude(created_at__date=today).exists()
    if prior_exists and not confirm:
        raise WarningException(
            "Same patient + medication on a different day; pass confirm=True",
            code="ORDER_CROSS_DAY_CONFIRM",
            warnings=["Same patient + medication exists on a different day"],
            detail={
                "patient_id": patient.id,
                "medication_name": medication_name,
            },
        )

    order = Order.objects.create(patient=patient, medication_name=medication_name)
    warnings = []
    if prior_exists:
        warnings.append("Same patient + medication exists on a different day")
    return order, warnings


def create_provider_patient_order(
    *,
    provider_name,
    provider_npi,
    patient_first_name,
    patient_last_name,
    patient_mrn,
    patient_date_of_birth,
    medication_name,
    confirm=False,
):
    from .serializers import validate_provider_patient_fields

    validate_provider_patient_fields(npi=provider_npi, mrn=patient_mrn)

    provider = resolve_provider(provider_name, provider_npi)
    patient, warnings = resolve_patient(
        patient_first_name,
        patient_last_name,
        patient_mrn,
        patient_date_of_birth,
    )
    if warnings and not confirm:
        raise WarningException(
            "Possible patient duplicate; pass confirm=True to continue",
            code="PATIENT_CONFIRM",
            warnings=warnings,
            detail={"mrn": patient_mrn, "patient_id": patient.id},
        )

    order, order_warnings = create_order(patient, medication_name, confirm=confirm)
    return {
        "provider": provider,
        "patient": patient,
        "order": order,
        "warnings": warnings + order_warnings,
    }


def create_care_plan(payload):
    # BP5: entered the business layer with a normalized dict
    debug_break("services.create_care_plan — entered with payload", payload=payload)

    logging.info(
        "create_care_plan: payload normalized patient_name_present=%s medication_present=%s additional_diagnosis_count=%s medication_history_count=%s records_present=%s",
        bool(payload.get("patient_first_name") or payload.get("patient_last_name")),
        bool(payload.get("medication_name")),
        len(payload.get("additional_diagnosis", [])),
        len(payload.get("medication_history", [])),
        bool(payload.get("patient_records")),
    )

    record = CarePlan.objects.create(
        status=CarePlan.STATUS_PENDING,
        history=[CarePlan.STATUS_PENDING],
        payload=payload,
    )
    logging.info("create_care_plan: record created careplan_id=%s status=%s", record.id, record.status)

    try:
        backend = get_execution_backend()
        backend.submit(str(record.id))
        record.queued_at = timezone.now()
        record.save(update_fields=["queued_at", "updated_at"])
        logging.info(
            "create_care_plan: execution backend queued careplan_id=%s backend=%s",
            record.id,
            backend.__class__.__name__,
        )
    except Exception as exc:
        logger.exception("create_care_plan: enqueue failed careplan_id=%s", record.id)
        record.status = CarePlan.STATUS_FAILED
        record.history = [*record.history, CarePlan.STATUS_FAILED]
        record.error = f"Failed to enqueue care plan: {exc}"
        record.save(update_fields=["status", "history", "error", "updated_at"])
        debug_break(
            "services.create_care_plan — enqueue failed, returning (record, False)",
            careplan_id=str(record.id),
            status=record.status,
            error=record.error,
        )
        return record, False

    logging.info("create_care_plan: response ready careplan_id=%s status=%s", record.id, record.status)
    debug_break(
        "services.create_care_plan — success, returning (record, True)",
        careplan_id=str(record.id),
        status=record.status,
        queued_at=str(record.queued_at),
    )
    return record, True


def get_care_plan(plan_id):
    try:
        return CarePlan.objects.get(id=plan_id)
    except (CarePlan.DoesNotExist, DjangoValidationError, ValueError):
        return None


def search_care_plans(query):
    results = []
    for record in CarePlan.objects.all():
        payload = record.payload
        haystack = " ".join(
            [
                str(record.id),
                record.status,
                payload.get("patient_first_name", ""),
                payload.get("patient_last_name", ""),
                payload.get("patient_mrn", ""),
                payload.get("referring_provider", ""),
                payload.get("patient_primary_diagnosis", ""),
                payload.get("medication_name", ""),
                " ".join(payload.get("additional_diagnosis", [])),
                " ".join(payload.get("medication_history", [])),
                payload.get("patient_records", ""),
            ]
        ).lower()
        if not query or query in haystack:
            results.append(record)

    return results
