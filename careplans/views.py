import json
import logging

from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import CarePlan
from .tasks import generate_care_plan_task

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "careplans/index.html")


def _record_to_dict(record):
    return {
        "id": str(record.id),
        "status": record.status,
        "history": record.history,
        "payload": record.payload,
        "care_plan": record.care_plan if record.status == "completed" else None,
        "error": record.error,
        "queued_at": record.queued_at.isoformat() if record.queued_at else None,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def _render_care_plan_text(record):
    care_plan = record.care_plan or {}
    payload = record.payload
    patient_name = f"{payload.get('patient_first_name', '')} {payload.get('patient_last_name', '')}".strip()
    lines = [
        f"Care Plan ID: {record.id}",
        f"Status: {record.status}",
        f"Patient: {patient_name}",
        f"MRN: {payload.get('patient_mrn', '')}",
        f"Medication: {payload.get('medication_name', '')}",
        "",
        "Problem list:",
        *[f"- {item}" for item in care_plan.get("problem_list", [])],
        "",
        "Goals:",
        *[f"- {item}" for item in care_plan.get("goals", [])],
        "",
        "Pharmacist interventions:",
        *[f"- {item}" for item in care_plan.get("pharmacist_interventions", [])],
        "",
        "Monitoring plan:",
        *[f"- {item}" for item in care_plan.get("monitoring_plan", [])],
        "",
    ]
    return "\n".join(lines)


def _parse_payload(request):
    if request.body:
        return json.loads(request.body.decode("utf-8"))
    return request.POST.dict()


def _normalize_payload(payload):
    additional_diagnosis = payload.get("additional_diagnosis", [])
    medication_history = payload.get("medication_history", [])

    if isinstance(additional_diagnosis, str):
        additional_diagnosis = [item.strip() for item in additional_diagnosis.split(",") if item.strip()]
    if isinstance(medication_history, str):
        medication_history = [item.strip() for item in medication_history.split(",") if item.strip()]

    return {
        "patient_first_name": payload.get("patient_first_name", ""),
        "patient_last_name": payload.get("patient_last_name", ""),
        "referring_provider": payload.get("referring_provider", ""),
        "referring_provider_npi": payload.get("referring_provider_npi", ""),
        "patient_mrn": payload.get("patient_mrn", ""),
        "patient_primary_diagnosis": payload.get("patient_primary_diagnosis", ""),
        "medication_name": payload.get("medication_name", ""),
        "additional_diagnosis": additional_diagnosis,
        "medication_history": medication_history,
        "patient_records": payload.get("patient_records", ""),
    }


@csrf_exempt
def create_care_plan(request):
    logging.info("create_care_plan: request received method=%s path=%s", request.method, request.path)
    payload = _normalize_payload(_parse_payload(request))
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
        return JsonResponse(_record_to_dict(record), status=503)

    logging.info("create_care_plan: response ready careplan_id=%s status=%s", record.id, record.status)
    return JsonResponse(
        {
            "message": "Received",
            "careplan_id": str(record.id),
            "status": record.status,
        },
        status=202,
    )


def get_care_plan(request, plan_id):
    try:
        record = CarePlan.objects.get(id=plan_id)
    except (CarePlan.DoesNotExist, ValidationError, ValueError):
        return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse(_record_to_dict(record))


def get_care_plan_status(request, plan_id):
    """Lightweight status endpoint for frontend polling."""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)

    try:
        record = CarePlan.objects.get(id=plan_id)
    except (CarePlan.DoesNotExist, ValidationError, ValueError):
        return JsonResponse({"error": "not found"}, status=404)

    response = {
        "id": str(record.id),
        "status": record.status,
        "content": record.care_plan if record.status == CarePlan.STATUS_COMPLETED else None,
        "error": record.error if record.status == CarePlan.STATUS_FAILED else None,
    }
    return JsonResponse(response)


def search_care_plans(request):
    query = request.GET.get("q", "").lower()
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
            results.append(_record_to_dict(record))

    return JsonResponse({"query": query, "results": results})


def download_care_plan(request, plan_id):
    try:
        record = CarePlan.objects.get(id=plan_id)
    except (CarePlan.DoesNotExist, ValidationError, ValueError):
        return JsonResponse({"error": "not found"}, status=404)

    response = HttpResponse(content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="care_plan_{plan_id}.txt"'
    response.write(_render_care_plan_text(record))
    return response
