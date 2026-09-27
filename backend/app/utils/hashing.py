"""Hashing utilities for content deduplication."""

from __future__ import annotations

import hashlib


def sha256_hex(data: bytes) -> str:
    """Return hex SHA-256 digest for binary data."""
    return hashlib.sha256(data).hexdigest()


def content_hash(text: str) -> str:
    """Return a short hash for text content (first 16 hex chars)."""
    return sha256_hex(text.encode("utf-8"))[:16]
