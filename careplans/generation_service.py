from __future__ import annotations

import logging

from .generator import generate_care_plan
from .models import CarePlan

logger = logging.getLogger(__name__)


def _append_status(record: CarePlan, status: str) -> None:
    history = list(record.history or [])
    if not history or history[-1] != status:
        history.append(status)
    record.history = history
    record.status = status


def run_care_plan_generation_once(careplan_id: str) -> CarePlan:
    record = CarePlan.objects.get(id=careplan_id)

    _append_status(record, CarePlan.STATUS_PROCESSING)
    record.error = None
    record.save(update_fields=["status", "history", "error", "updated_at"])
    logger.info("run_care_plan_generation_once: processing careplan_id=%s", careplan_id)

    try:
        care_plan = generate_care_plan(record.payload)
    except Exception as exc:
        logger.exception(
            "run_care_plan_generation_once: generation failed careplan_id=%s",
            careplan_id,
        )
        record.error = str(exc)
        record.save(update_fields=["error", "updated_at"])
        raise

    _append_status(record, CarePlan.STATUS_COMPLETED)
    record.care_plan = care_plan
    record.error = None
    record.save(update_fields=["status", "history", "care_plan", "error", "updated_at"])
    logger.info("run_care_plan_generation_once: completed careplan_id=%s", careplan_id)
    return record

