#!/usr/bin/env python3
"""Utilities for loading, cleaning, and saving GradCafe application data."""

from __future__ import annotations

import json
import re
import warnings
from typing import Any, Dict, Iterable, List, Optional

import urllib3
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# HTTP client for LLM API calls
_http = urllib3.PoolManager()


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


def _standardize_university_with_llm(
    entry: Dict[str, Any], 
    api_url: str = "http://localhost:8000/standardize"
) -> Dict[str, Any]:
    """
    Call the LLM hosting API to standardize the university and program fields.
    
    Args:
        entry: A single entry dictionary with 'university' and 'program_name' fields
        api_url: The URL of the LLM standardization API endpoint
        
    Returns:
        The entry dictionary with added 'llm-generated-university' and 
        'llm-generated-program' fields, or the original entry if API call fails
    """
    try:
        # Send single entry wrapped in a list as the API expects a JSON array
        payload = json.dumps([entry]).encode("utf-8")
        resp = _http.request(
            "POST",
            api_url,
            body=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status == 200:
            result = json.loads(resp.data.decode("utf-8"))
            # API returns a list, extract the first (and only) entry
            if isinstance(result, list) and len(result) > 0:
                return result[0]
        else:
            print(f"[llm-api] HTTP {resp.status} from {api_url}")
    except Exception as e:
        print(f"[llm-api] error calling {api_url}: {e}")
    
    return entry


def _standardize_with_llm(
    data: List[Dict[str, Any]], 
    api_url: str = "http://localhost:8000/standardize",
    output_path: Optional[str] = None,
    flush_every: int = 100
) -> List[Dict[str, Any]]:
    """
    Standardize university and program fields for all entries using LLM API.
    
    Args:
        data: List of entry dictionaries
        api_url: The URL of the LLM standardization API endpoint
        output_path: If provided, save progress every flush_every entries
        flush_every: Number of entries to process before saving progress
        
    Returns:
        List of entries with added 'llm-generated-university' and 
        'llm-generated-program' fields
    """
    results = []
    for i, entry in enumerate(data, 1):
        standardized = _standardize_university_with_llm(entry, api_url)
        results.append(standardized)
        if i % 10 == 0:
            print(f"[standardize] processed {i}/{len(data)} entries")
        # Flush to disk every flush_every entries
        if output_path and i % flush_every == 0:
            save_data(results, output_path)
            print(f"[standardize] flushed progress to {output_path}")
    print(f"[standardize] completed {len(results)} entries")
    return results


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Clean and standardize GradCafe application data")
    parser.add_argument("--input", help="Input JSON file", default="applicant_data.json")
    parser.add_argument("--output", help="Output JSON file", default="applicant_data_clean.json")
    parser.add_argument("--api", help="LLM API URL", default="http://localhost:8000/standardize")
    parser.add_argument("--standardize", action="store_true", help="Standardize university/program with LLM")
    args = parser.parse_args()

    print(f"[clean] loading data from {args.input}")
    data = load_data(args.input)
    
    print(f"[clean] cleaning {len(data)} entries")
    cleaned = clean_data(data)
    
    if args.standardize:
        print(f"[clean] standardizing with LLM API at {args.api}")
        # Check if output already exists and resume from there
        if os.path.exists(args.output):
            print(f"[clean] resuming from existing {args.output}")
            existing = load_data(args.output)
            # Skip entries that already have LLM fields
            existing_count = len([e for e in existing if 'llm-generated-university' in e])
            if existing_count > 0:
                print(f"[clean] found {existing_count} already processed entries")
                cleaned = existing + cleaned[existing_count:]
        cleaned = _standardize_with_llm(cleaned, args.api, output_path=args.output, flush_every=100)
    
    print(f"[clean] saving to {args.output}")
    save_data(cleaned, args.output)
    print("Done.")
