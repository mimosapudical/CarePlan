import logging

from django.core.management.base import BaseCommand, CommandError

from careplans.generation_service import run_care_plan_generation_once
from careplans.models import CarePlan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate a single care plan attempt without any retry loop."

    def add_arguments(self, parser):
        parser.add_argument("careplan_id", help="Care plan UUID")

    def handle(self, *args, **options):
        careplan_id = options["careplan_id"]
        logger.info("generate_careplan_once: starting careplan_id=%s", careplan_id)

        try:
            record = run_care_plan_generation_once(careplan_id)
        except CarePlan.DoesNotExist as exc:
            logger.error("generate_careplan_once: care plan not found id=%s", careplan_id)
            raise CommandError(f"Care plan not found: {careplan_id}") from exc
        except Exception as exc:
            logger.exception("generate_careplan_once: failed careplan_id=%s", careplan_id)
            raise CommandError(f"Generation failed for {careplan_id}: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Completed: {record.id}"))
        return str(record.id)

