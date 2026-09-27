"""Structured logging setup with request-level context."""

import logging
import sys
import time
from contextvars import ContextVar
from uuid import uuid4

from app.core.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


def generate_request_id() -> str:
    return uuid4().hex[:12]


def setup_logging() -> None:
    fmt = (
        "%(asctime)s | %(levelname)-8s | %(request_id)s | "
        "%(name)s | %(message)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)


class TimingContext:
    """Simple context manager to measure elapsed ms."""

    def __init__(self) -> None:
        self.elapsed_ms: float = 0

    def __enter__(self) -> "TimingContext":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self.elapsed_ms = round((time.perf_counter() - self._start) * 1000, 1)
