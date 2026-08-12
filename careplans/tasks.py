import logging

from celery import shared_task

from careplans.generation_service import run_care_plan_generation_once
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
        record = run_care_plan_generation_once(careplan_id)
    except CarePlan.DoesNotExist:
        logger.error("generate_care_plan_task: care plan not found id=%s", careplan_id)
        return "not_found"
    except Exception as exc:
        record = CarePlan.objects.filter(id=careplan_id).first()
        logger.exception(
            "generate_care_plan_task: generation failed careplan_id=%s attempt=%s",
            careplan_id,
            self.request.retries + 1,
        )
        if record is not None and self.request.retries >= self.max_retries:
            _append_status(record, CarePlan.STATUS_FAILED)
            record.error = str(exc)
            record.save(update_fields=["status", "history", "error", "updated_at"])
            logger.error("generate_care_plan_task: giving up careplan_id=%s", careplan_id)
        raise
    logger.info("generate_care_plan_task: completed careplan_id=%s", careplan_id)
    return "completed"
