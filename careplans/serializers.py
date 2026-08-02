import json

from .debug_trace import debug_break
from .models import CarePlan


def parse_payload(request):
    if request.body:
        raw = json.loads(request.body.decode("utf-8"))
    else:
        raw = request.POST.dict()
    # BP2: HTTP bytes/form → Python dict（仍是前端原始字段）
    debug_break("serializers.parse_payload — HTTP → raw dict", raw=raw)
    return raw


def normalize_payload(payload):
    additional_diagnosis = payload.get("additional_diagnosis", [])
    medication_history = payload.get("medication_history", [])

    if isinstance(additional_diagnosis, str):
        additional_diagnosis = [item.strip() for item in additional_diagnosis.split(",") if item.strip()]
    if isinstance(medication_history, str):
        medication_history = [item.strip() for item in medication_history.split(",") if item.strip()]

    normalized = {
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
    # BP3: 前端原始 dict → 后端规范 payload（字符串列表已拆开）
    debug_break(
        "serializers.normalize_payload — raw dict → normalized payload",
        before_additional=payload.get("additional_diagnosis"),
        after_additional=normalized["additional_diagnosis"],
        normalized=normalized,
    )
    return normalized


def record_to_dict(record):
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


def status_to_dict(record):
    return {
        "id": str(record.id),
        "status": record.status,
        "content": record.care_plan if record.status == CarePlan.STATUS_COMPLETED else None,
        "error": record.error if record.status == CarePlan.STATUS_FAILED else None,
    }


def render_care_plan_text(record):
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
