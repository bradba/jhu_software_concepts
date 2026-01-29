#!/usr/bin/env python3
"""Utilities for loading, cleaning, and saving GradCafe application data."""

from __future__ import annotations

import json
import re
import warnings
from typing import Any, Dict, Iterable, List, Optional

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


def _strip_html(value: str) -> str:
    """Remove any HTML tags/entities and normalize whitespace."""
    if not value:
        return value
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_value(value: Any, missing_value: Optional[str]) -> Optional[str]:
    """Normalize missing/empty values and strip HTML from strings."""
    if value is None:
        return missing_value
    if isinstance(value, str):
        cleaned = _strip_html(value)
        return cleaned if cleaned else missing_value
    return value  # non-string values are returned as-is


def _clean_record(record: Dict[str, Any], missing_value: Optional[str]) -> Dict[str, Any]:
    """Clean a single record by removing HTML and normalizing missing values."""
    cleaned: Dict[str, Any] = {}
    for key, value in record.items():
        cleaned[key] = _normalize_value(value, missing_value)
    return cleaned


def _clean_comment_text(text: Optional[str]) -> Optional[str]:
    """Remove badge-like tokens and boilerplate from comments text."""
    if not text:
        return None
    cleaned = _strip_html(text)
    for pattern in [
        r"(Fall|Spring|Summer|Winter)\s+\d{4}",
        r"International",
        r"American",
        r"Domestic",
        r"GPA\s+[\d\.]+",
        r"GRE\s+(?:General\s+)?\d+",
        r"GRE\s+V\s*\d+",
        r"AW\s+[\d\.]+",
        r"Accepted on \d+\s+\w+",
        r"Rejected on \d+\s+\w+",
    ]:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    cleaned = " ".join(cleaned.split())
    if len(cleaned) > 15 and not all(c in ".,;:!? " for c in cleaned):
        return cleaned[:500]
    return None


def load_data(path: str) -> List[Dict[str, Any]]:
    """Load application data from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Expected a list of records in the JSON file.")
    return data


def clean_data(data: Iterable[Dict[str, Any]], missing_value: Optional[str] = None) -> List[Dict[str, Any]]:
    """Convert data into a structured, cleaned format.

    - Strips HTML from all string fields.
    - Normalizes missing/empty values to a consistent format (default: None).
    """
    return [_clean_record(record, missing_value) for record in data]


def save_data(data: List[Dict[str, Any]], path: str) -> None:
    """Save cleaned data into a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
