import logging

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from . import serializers, services
from .debug_trace import debug_break
from .exceptions import BlockError
from .models import CarePlan


def index(request):
    return render(request, "careplans/index.html")


@csrf_exempt
def create_care_plan(request):
    logging.info("create_care_plan: request received method=%s path=%s", request.method, request.path)
    # BP1: urls.py just routed the request to this view
    debug_break(
        "views.create_care_plan — entered from urls",
        method=request.method,
        path=request.path,
        raw_body=request.body.decode("utf-8", errors="replace"),
    )

    payload = serializers.normalize_payload(serializers.parse_payload(request))
    # BP4: serializers turned the HTTP body into a business payload for services
    debug_break(
        "views.create_care_plan — after serializers, before services",
        payload=payload,
    )

    record, queued = services.create_care_plan(payload)
    # BP6: services wrote to the DB and enqueued; about to build the HTTP response
    debug_break(
        "views.create_care_plan — after services, before response",
        careplan_id=str(record.id),
        status=record.status,
        queued=queued,
    )

    if not queued:
        return JsonResponse(serializers.record_to_dict(record), status=503)

    return JsonResponse(
        {
            "message": "Received",
            "careplan_id": str(record.id),
            "status": record.status,
        },
        status=202,
    )


def get_care_plan(request, plan_id):
    record = services.get_care_plan(plan_id)
    if record is None:
        return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse(serializers.record_to_dict(record))


def get_care_plan_status(request, plan_id):
    """Lightweight status endpoint for frontend polling."""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)

    record = services.get_care_plan(plan_id)
    if record is None:
        return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse(serializers.status_to_dict(record))


def search_care_plans(request):
    query = request.GET.get("q", "").lower()
    records = services.search_care_plans(query)
    results = [serializers.record_to_dict(record) for record in records]
    return JsonResponse({"query": query, "results": results})


def download_care_plan(request, plan_id):
    record = services.get_care_plan(plan_id)
    if record is None:
        return JsonResponse({"error": "not found"}, status=404)

    response = HttpResponse(content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="care_plan_{plan_id}.txt"'
    response.write(serializers.render_care_plan_text(record))
    return response


def get_ops_care_plans(request):
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    status = request.GET.get("status") or None
    if status and status not in dict(CarePlan.STATUS_CHOICES):
        return JsonResponse({"error": "invalid status"}, status=400)
    try:
        stale_minutes = int(request.GET.get("stale_minutes", "30"))
        if stale_minutes < 1:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({"error": "stale_minutes must be a positive integer"}, status=400)
    records = services.get_ops_care_plans(status=status, stale_minutes=stale_minutes)
    return JsonResponse({"results": [serializers.ops_record_to_dict(record) for record in records]})


@csrf_exempt
def retry_care_plan(request, plan_id):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        record, queued = services.retry_failed_care_plan(plan_id)
    except BlockError:
        return JsonResponse({"error": "Only failed care-plan jobs can be retried"}, status=409)
    if record is None:
        return JsonResponse({"error": "not found"}, status=404)
    if not queued:
        return JsonResponse({"error": "Care-plan retry could not be queued"}, status=503)
    return JsonResponse(serializers.ops_record_to_dict(record), status=202)
