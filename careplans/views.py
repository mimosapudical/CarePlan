import logging

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from . import serializers, services
from .debug_trace import debug_break


def index(request):
    return render(request, "careplans/index.html")


@csrf_exempt
def create_care_plan(request):
    logging.info("create_care_plan: request received method=%s path=%s", request.method, request.path)
    # BP1: urls.py 刚把请求路由到这个 view
    debug_break(
        "views.create_care_plan — entered from urls",
        method=request.method,
        path=request.path,
        raw_body=request.body.decode("utf-8", errors="replace"),
    )

    payload = serializers.normalize_payload(serializers.parse_payload(request))
    # BP4: serializers 已把 HTTP body 转成业务 payload，准备交给 services
    debug_break(
        "views.create_care_plan — after serializers, before services",
        payload=payload,
    )

    record, queued = services.create_care_plan(payload)
    # BP6: services 已写库并入队，准备组装 HTTP 响应
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
