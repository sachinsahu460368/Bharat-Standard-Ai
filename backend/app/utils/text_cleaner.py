"""Text cleaning utilities for procurement documents."""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Clean extracted document text while preserving structure."""
    if not text:
        return ""

    # Normalize unicode whitespace
    text = text.replace(" ", " ")
    text = text.replace("​", "")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse runs of 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove trailing whitespace per line
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    # Collapse runs of spaces (but not newlines)
    text = re.sub(r"[^\S\n]+", " ", text)

    return text.strip()


def normalize_standard_reference(ref: str) -> str:
    """Normalize an Indian Standard reference for matching.

    Examples:
        'IS 10322 (Part 5/Sec 2) : 2012' -> 'IS 10322'
        'IS10322:2012' -> 'IS 10322'
        'is 1234' -> 'IS 1234'
    """
    ref = ref.strip().upper()
    # Remove year portion
    ref = re.sub(r"\s*:\s*\d{4}\s*$", "", ref)
    # Remove part/section info
    ref = re.sub(r"\s*\(.*?\)\s*", " ", ref)
    # Ensure space after 'IS'
    ref = re.sub(r"^IS(\d)", r"IS \1", ref)
    # Collapse whitespace
    ref = re.sub(r"\s+", " ", ref).strip()
    return ref


def extract_is_references(text: str) -> list[str]:
    """Extract IS/BIS standard references from text.

    Matches patterns like:
        IS 1234, IS 1234:2020, IS 10322 (Part 5), IS/IEC 60947
    """
    pattern = r"IS(?:/[A-Z]+)?\s*\d{1,5}(?:\s*\([^)]*\))?(?:\s*:\s*\d{4})?"
    matches = re.findall(pattern, text, re.IGNORECASE)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for m in matches:
        normalized = normalize_standard_reference(m)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(m.strip())
    return unique
