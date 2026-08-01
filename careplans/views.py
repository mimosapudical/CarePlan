import json
import logging
import uuid

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .generator import generate_care_plan
from .store import CARE_PLAN_STORE, STORE_LOCK, CarePlanRecord

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "careplans/index.html")


def _record_to_dict(record):
    return {
        "id": record.id,
        "status": record.status,
        "history": record.history,
        "payload": record.payload,
        "care_plan": record.care_plan if record.status == "completed" else None,
        "error": record.error,
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
    plan_id = uuid.uuid4().hex
    record = CarePlanRecord(id=plan_id, payload=payload)

    with STORE_LOCK:
        record.status = "pending"
        record.history.append("pending")
        CARE_PLAN_STORE[plan_id] = record
    logging.info("create_care_plan: record created plan_id=%s status=%s", plan_id, record.status)

    try:
        with STORE_LOCK:
            record.status = "processing"
            record.history.append("processing")
        logging.info("create_care_plan: calling generate_care_plan plan_id=%s", plan_id)

        care_plan = generate_care_plan(payload)
        logging.info(
            "create_care_plan: generate_care_plan returned plan_id=%s sections=%s",
            plan_id,
            list(care_plan.keys()),
        )

        with STORE_LOCK:
            record.status = "completed"
            record.history.append("completed")
            record.care_plan = care_plan
        logging.info("create_care_plan: record completed plan_id=%s status=%s", plan_id, record.status)
    except Exception as exc:
        logger.exception("create_care_plan: failed plan_id=%s", plan_id)
        with STORE_LOCK:
            record.status = "failed"
            record.history.append("failed")
            record.error = str(exc)

    logging.info("create_care_plan: response ready plan_id=%s status=%s", plan_id, record.status)
    return JsonResponse(_record_to_dict(record))


def get_care_plan(request, plan_id):
    with STORE_LOCK:
        record = CARE_PLAN_STORE.get(plan_id)

    if not record:
        return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse(_record_to_dict(record))


def search_care_plans(request):
    query = request.GET.get("q", "").lower()
    with STORE_LOCK:
        records = list(CARE_PLAN_STORE.values())

    results = []
    for record in records:
        payload = record.payload
        haystack = " ".join(
            [
                record.id,
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
    with STORE_LOCK:
        record = CARE_PLAN_STORE.get(plan_id)

    if not record:
        return JsonResponse({"error": "not found"}, status=404)

    response = HttpResponse(content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="care_plan_{plan_id}.txt"'
    response.write(_render_care_plan_text(record))
    return response
