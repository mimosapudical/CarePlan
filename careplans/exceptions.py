"""Unified application exceptions.

All business/validation failures should raise a BaseAppException subclass.
Views only raise; careplans.exception_handler (and middleware) render JSON.
"""


class BaseAppException(Exception):
    """Single shape for every abnormal API outcome."""

    type = "error"
    default_code = "ERROR"
    default_message = "An error occurred"
    http_status = 500

    def __init__(
        self,
        message=None,
        *,
        code=None,
        detail=None,
        warnings=None,
        http_status=None,
    ):
        self.message = message if message is not None else self.default_message
        self.code = code if code is not None else self.default_code
        self.detail = detail
        self.warnings = list(warnings) if warnings else []
        if http_status is not None:
            self.http_status = http_status
        super().__init__(self.message)

    def to_dict(self):
        return {
            "type": self.type,
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
            "http_status": self.http_status,
            "warnings": self.warnings,
        }


class ValidationError(BaseAppException):
    """Input/format problems (serializer). HTTP 400."""

    type = "validation"
    default_code = "VALIDATION_ERROR"
    default_message = "Validation failed"
    http_status = 400


class BlockError(BaseAppException):
    """Hard business rule violation. HTTP 409."""

    type = "block"
    default_code = "BLOCKED"
    default_message = "Request blocked by business rules"
    http_status = 409


class WarningException(BaseAppException):
    """Soft conflict: client may confirm and retry. HTTP 200 + warnings."""

    type = "warning"
    default_code = "WARNING"
    default_message = "Confirmation required to continue"
    http_status = 200


# Backward-compatible aliases for earlier duplicate-detection names
ConflictError = BlockError
ConfirmationRequired = WarningException
