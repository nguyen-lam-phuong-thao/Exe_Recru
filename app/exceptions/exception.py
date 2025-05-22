from typing import TypeVar

from fastapi import HTTPException

from app.middleware.translation_manager import _
from fastapi import status

T = TypeVar("T")


class CustomHTTPException(HTTPException):
    """CustomHTTPException"""

    def __init__(self, status_code: int = 200, message: str = _("error_occurred")):
        super().__init__(status_code=status_code, detail=message)
        self.message = message


class UnauthorizedException(CustomHTTPException):
    """UnauthorizedException"""

    def __init__(self, message: str = _("unauthorized_access")):
        super().__init__(status_code=401, message=message)


class ForbiddenException(CustomHTTPException):
    """ForbiddenException"""

    def __init__(self, message=_("forbidden_action")):
        super().__init__(status_code=403, message=message)


class NotFoundException(CustomHTTPException):
    """NotFoundException"""

    def __init__(self, resource_name: str = "resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=_("resource_not_found").format(resource_name),
        )


class ValidationException(CustomHTTPException):
    """ValidationException"""

    def __init__(self, message=_("validation_failed")):
        super().__init__(status_code=422, message=message)


class QuestionGenerationException(CustomHTTPException):
    """QuestionGenerationException"""

    def __init__(self, message=_("error_generating_questions")):
        super().__init__(status_code=500, message=message)


class KnowledgeBaseConnectionException(CustomHTTPException):
    """KnowledgeBaseConnectionException"""

    def __init__(self, message=_("error_connecting_knowledge_base")):
        super().__init__(status_code=503, message=message)


class SelfReflectionException(CustomHTTPException):
    """SelfReflectionException"""

    def __init__(self, message=_("error_in_self_reflection")):
        super().__init__(status_code=500, message=message)
