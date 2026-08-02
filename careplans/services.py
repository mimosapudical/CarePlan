import logging

from django.core.exceptions import ValidationError
from django.utils import timezone

from .debug_trace import debug_break
from .models import CarePlan
from .tasks import generate_care_plan_task

logger = logging.getLogger(__name__)


def create_care_plan(payload):
    # BP5: 进入业务层，拿到的已是规范化 dict
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
        generate_care_plan_task.delay(str(record.id))
        record.queued_at = timezone.now()
        record.save(update_fields=["queued_at", "updated_at"])
        logging.info("create_care_plan: celery task queued careplan_id=%s", record.id)
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
    except (CarePlan.DoesNotExist, ValidationError, ValueError):
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
