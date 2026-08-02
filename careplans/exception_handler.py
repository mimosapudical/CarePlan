"""Turn exceptions into one JSON shape for the frontend.

Frontend rule of thumb:
  - success payload (no abnormal `type`) → ok
  - type == "validation" → 400, fix input
  - type == "block" → 409, cannot proceed
  - type == "warning" → 200, show warnings; retry with confirm=True
"""

from django.http import JsonResponse

from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .exceptions import BaseAppException, ValidationError


def _drf_detail_to_dict(detail):
    if isinstance(detail, list):
        return [str(item) for item in detail]
    if isinstance(detail, dict):
        return {key: _drf_detail_to_dict(value) for key, value in detail.items()}
    return str(detail)


def render_app_exception(exc: BaseAppException) -> JsonResponse:
    """For Django middleware / plain views."""
    return JsonResponse(exc.to_dict(), status=exc.http_status)


def exception_handler(exc, context):
    """DRF EXCEPTION_HANDLER: BaseAppException + DRF ValidationError bridge."""
    if isinstance(exc, BaseAppException):
        return Response(exc.to_dict(), status=exc.http_status)

    if isinstance(exc, DRFValidationError):
        app_exc = ValidationError(
            message="Validation failed",
            code="VALIDATION_ERROR",
            detail=_drf_detail_to_dict(exc.detail),
        )
        return Response(app_exc.to_dict(), status=app_exc.http_status)

    return drf_exception_handler(exc, context)


class AppExceptionMiddleware:
    """Catch BaseAppException in plain Django views (non-DRF)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, BaseAppException):
            return render_app_exception(exception)
        return None
