import logging
import time

import redis
from django.conf import settings
from django.core.management.base import BaseCommand

from careplans.generator import generate_care_plan
from careplans.models import CarePlan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Pull careplan_id from Redis, call LLM, and save the care plan to the database."

    def handle(self, *args, **options):
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        queue_name = settings.CAREPLAN_QUEUE_NAME

        self.stdout.write(self.style.SUCCESS(f"Worker started. Waiting on queue: {queue_name}"))
        logger.info("process_careplan_queue: worker started queue=%s", queue_name)

        while True:
            try:
                item = client.brpop(queue_name, timeout=5)
            except redis.RedisError as exc:
                logger.exception("process_careplan_queue: redis error: %s", exc)
                self.stderr.write(self.style.ERROR(f"Redis error: {exc}"))
                time.sleep(2)
                continue

            if item is None:
                continue

            _, careplan_id = item
            self.stdout.write(f"Got task: {careplan_id}")
            self._process_one(careplan_id)

    def _process_one(self, careplan_id: str) -> None:
        try:
            record = CarePlan.objects.get(id=careplan_id)
        except CarePlan.DoesNotExist:
            logger.error("process_careplan_queue: care plan not found id=%s", careplan_id)
            self.stderr.write(self.style.ERROR(f"Care plan not found: {careplan_id}"))
            return

        record.status = CarePlan.STATUS_PROCESSING
        record.history = [*record.history, CarePlan.STATUS_PROCESSING]
        record.error = None
        record.save(update_fields=["status", "history", "error", "updated_at"])
        logger.info("process_careplan_queue: processing careplan_id=%s", careplan_id)

        try:
            care_plan = generate_care_plan(record.payload)
        except Exception as exc:
            logger.exception("process_careplan_queue: generation failed careplan_id=%s", careplan_id)
            record.status = CarePlan.STATUS_FAILED
            record.history = [*record.history, CarePlan.STATUS_FAILED]
            record.error = str(exc)
            record.save(update_fields=["status", "history", "error", "updated_at"])
            self.stderr.write(self.style.ERROR(f"Failed {careplan_id}: {exc}"))
            return

        record.status = CarePlan.STATUS_COMPLETED
        record.history = [*record.history, CarePlan.STATUS_COMPLETED]
        record.care_plan = care_plan
        record.error = None
        record.save(update_fields=["status", "history", "care_plan", "error", "updated_at"])
        logger.info("process_careplan_queue: completed careplan_id=%s", careplan_id)
        self.stdout.write(self.style.SUCCESS(f"Completed: {careplan_id}"))
