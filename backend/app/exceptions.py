from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class MailMindException(HTTPException):
    """Base exception for Mail Mind with structured error format"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.metadata = metadata or {}
        super().__init__(status_code=status_code, detail=detail)

class ValidationError(MailMindException):
    """Validation error (400)"""
    def __init__(self, detail: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR",
            metadata=metadata
        )

class NotFoundError(MailMindException):
    """Not found error (404)"""
    def __init__(self, detail: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
            metadata=metadata
        )

class ConnectionError(MailMindException):
    """Email connection error (502)"""
    def __init__(self, detail: str, provider: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            error_code="CONNECTION_ERROR",
            metadata={"provider": provider} if provider else {}
        )

class RateLimitError(MailMindException):
    """Rate limit error (429)"""
    def __init__(self, detail: str, retry_after: Optional[int] = None):
        metadata = {}
        if retry_after:
            metadata["retry_after"] = retry_after
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_ERROR",
            metadata=metadata
        )

class ConfigurationError(MailMindException):
    """Configuration error (500)"""
    def __init__(self, detail: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="CONFIGURATION_ERROR",
            metadata=metadata
        )

