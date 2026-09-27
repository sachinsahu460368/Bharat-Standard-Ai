"""Tests for text cleaning and IS reference extraction utilities."""

from app.utils.text_cleaner import (
    clean_text,
    extract_is_references,
    normalize_standard_reference,
)


def test_clean_text_normalizes_whitespace():
    raw = "Hello   world\r\n\r\n\r\nfoo"
    assert clean_text(raw) == "Hello world\n\nfoo"


def test_clean_text_empty():
    assert clean_text("") == ""


def test_normalize_standard_reference():
    assert normalize_standard_reference("IS 10322 (Part 5/Sec 2) : 2012") == "IS 10322"
    assert normalize_standard_reference("IS10322:2012") == "IS 10322"
    assert normalize_standard_reference("is 1234") == "IS 1234"


def test_extract_is_references():
    text = (
        "The luminaires must conform to IS 10322, IS 16102 (Part 1), "
        "and IS 16107:2018. Also reference IS/IEC 60947."
    )
    refs = extract_is_references(text)
    assert len(refs) == 4
    # Check normalized form is present
    normed = [normalize_standard_reference(r) for r in refs]
    assert "IS 10322" in normed
    assert "IS 16102" in normed


def test_extract_is_references_no_match():
    assert extract_is_references("No standard references here.") == []
