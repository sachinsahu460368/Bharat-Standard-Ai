"""File validation utilities."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import EmptyFileError, FileTooLargeError, InvalidFileError

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def sanitize_filename(filename: str) -> str:
    """Remove path separators and null bytes from filename."""
    name = Path(filename).name
    name = name.replace("\x00", "")
    # Keep only safe characters
    safe = "".join(
        c for c in name if c.isalnum() or c in (".", "-", "_", " ")
    )
    return safe or "unnamed"


def validate_file(
    filename: str,
    content_type: str | None,
    size: int,
) -> str:
    """Validate uploaded file. Returns the sanitized filename.

    Raises InvalidFileError, FileTooLargeError, or EmptyFileError.
    """
    if size == 0:
        raise EmptyFileError()

    if size > settings.max_file_size_bytes:
        raise FileTooLargeError(
            f"File size {size / (1024*1024):.1f} MB exceeds "
            f"limit of {settings.max_file_size_mb} MB."
        )

    safe_name = sanitize_filename(filename)
    ext = Path(safe_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileError(
            f"Extension '{ext}' is not supported. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Check MIME type if provided
    if content_type:
        # Normalize — some clients send charsets
        base_type = content_type.split(";")[0].strip().lower()
        # Also accept application/octet-stream as a fallback
        if base_type not in ALLOWED_MIME_TYPES and base_type != "application/octet-stream":
            # Try guessing from extension
            guessed, _ = mimetypes.guess_type(safe_name)
            if guessed and guessed not in ALLOWED_MIME_TYPES:
                raise InvalidFileError(
                    f"MIME type '{content_type}' is not supported."
                )

    return safe_name
