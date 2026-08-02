import logging

from celery import shared_task

from careplans.generator import generate_care_plan
from careplans.models import CarePlan

logger = logging.getLogger(__name__)


def _append_status(record: CarePlan, status: str) -> None:
    history = list(record.history or [])
    if not history or history[-1] != status:
        history.append(status)
    record.history = history
    record.status = status


@shared_task(
    bind=True,
    name="careplans.generate_care_plan",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def generate_care_plan_task(self, careplan_id: str) -> str:
    """Generate a care plan via LLM and persist status/result to the database."""
    logger.info(
        "generate_care_plan_task: start careplan_id=%s attempt=%s/%s",
        careplan_id,
        self.request.retries + 1,
        self.max_retries + 1,
    )

    try:
        record = CarePlan.objects.get(id=careplan_id)
    except CarePlan.DoesNotExist:
        logger.error("generate_care_plan_task: care plan not found id=%s", careplan_id)
        return "not_found"

    _append_status(record, CarePlan.STATUS_PROCESSING)
    record.error = None
    record.save(update_fields=["status", "history", "error", "updated_at"])

    try:
        care_plan = generate_care_plan(record.payload)
    except Exception as exc:
        logger.exception(
            "generate_care_plan_task: generation failed careplan_id=%s attempt=%s",
            careplan_id,
            self.request.retries + 1,
        )
        if self.request.retries >= self.max_retries:
            _append_status(record, CarePlan.STATUS_FAILED)
            record.error = str(exc)
            record.save(update_fields=["status", "history", "error", "updated_at"])
            logger.error("generate_care_plan_task: giving up careplan_id=%s", careplan_id)
        raise

    _append_status(record, CarePlan.STATUS_COMPLETED)
    record.care_plan = care_plan
    record.error = None
    record.save(update_fields=["status", "history", "care_plan", "error", "updated_at"])
    logger.info("generate_care_plan_task: completed careplan_id=%s", careplan_id)
    return "completed"
