"""Custom exceptions with structured error responses."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidFileError(AppError):
    def __init__(self, message: str = "Unsupported file type.") -> None:
        super().__init__("INVALID_FILE", message, 415)


class FileTooLargeError(AppError):
    def __init__(self, message: str = "File exceeds maximum size.") -> None:
        super().__init__("FILE_TOO_LARGE", message, 413)


class EmptyFileError(AppError):
    def __init__(self, message: str = "Uploaded file is empty.") -> None:
        super().__init__("EMPTY_FILE", message, 400)


class ExtractionError(AppError):
    def __init__(self, message: str = "Failed to extract text from document.") -> None:
        super().__init__("EXTRACTION_ERROR", message, 422)


class StandardNotFoundError(AppError):
    def __init__(self, standard_id: str) -> None:
        super().__init__(
            "STANDARD_NOT_FOUND",
            f"Standard '{standard_id}' not found.",
            404,
        )


class ServiceUnavailableError(AppError):
    def __init__(self, service: str = "AI") -> None:
        super().__init__(
            "SERVICE_UNAVAILABLE",
            f"{service} service is currently unavailable.",
            503,
        )


class ValidationError(AppError):
    def __init__(self, message: str = "Validation error.") -> None:
        super().__init__("VALIDATION_ERROR", message, 422)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
