#!/usr/bin/env python3
"""
This script fetches applicant posts from The Grad Cafe.
It extracts relevant fields from each post and saves the data in JSON format.
"""

from __future__ import annotations

import json
import re
import time
from typing import List, Dict, Optional

from urllib import parse as urlparse
import urllib3
from bs4 import BeautifulSoup
from clean import _clean_comment_text

# Constants
USER_AGENT = "GradCafeScraper/1.0 (+https://example.com/)"
DEFAULT_BASE = "https://www.thegradcafe.com/"
JSON_OUTPUT = "applicant_data.json"

# Keep a single PoolManager
_http = urllib3.PoolManager()


def _fetch_url(url: str, sleep: float = 1.0) -> Optional[str]:
    """Fetch a URL. Returns HTML text or None."""
    resp = _http.request("GET", url, headers={"User-Agent": USER_AGENT})
    time.sleep(sleep)
    if resp.status != 200:
        print(f"[http] status {resp.status} for {url}")
        return None
    return resp.data.decode("utf-8", errors="replace")


def _extract_comments_from_result_page(result_url: str) -> Optional[str]:
    """Fetch a result page and extract the Notes/Comments field if present."""
    html = _fetch_url(result_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    for dt in soup.find_all("dt"):
        label = dt.get_text(" ", strip=True).lower()
        if label in {"notes", "note", "comments", "comment"}:
            dd = dt.find_next_sibling("dd")
            if dd:
                text = dd.get_text(" ", strip=True)
                if text:
                    return text

    return None


def _extract_entries_from_page(html: str, source_url: str) -> List[Dict[str, Optional[str]]]:
    """
    Extract individual entries from a results page by parsing the HTML table.
    The GradCafe results are displayed in a table where each entry uses 2 rows:
    - Row 1: University, Program (with degree), Added On date, Decision, Actions
    - Row 2: Additional details (term, citizenship, GPA, GRE, etc.) and optional comments

    Returns:
        List of entry dictionaries
    """
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        return []

    rows = table.find_all('tr')
    entries = []
    
    i = 1  # Skip header row
    while i < len(rows):
        row1 = rows[i]
    
        # Check if this is a data row (not header, has td elements)
        cells = row1.find_all('td')
        if len(cells) < 4:
            i += 1
            continue
        
        # Extract from row 1: university, program, degree, date, decision
        university = cells[0].get_text(strip=True)
    
        # Program cell contains both program name and degree
        program_cell = cells[1]
        program_spans = program_cell.find_all('span')
        program = program_spans[0].get_text(strip=True) if len(program_spans) > 0 else ""
        degree = program_spans[1].get_text(strip=True) if len(program_spans) > 1 else None
    
        date_posted = cells[2].get_text(strip=True) if len(cells) > 2 else None
    
        # Decision cell (Accepted/Rejected on date)
        decision_text = cells[3].get_text(strip=True) if len(cells) > 3 else ""
    
        # Parse decision and date from decision_text (e.g., "Rejected on 28 Jan")
        status_match = re.search(r'(Accepted|Rejected|Interview|Wait\s?listed)', decision_text, re.IGNORECASE)
        status = status_match.group(1) if status_match else None
    
        accepted_date = None
        rejected_date = None
        if status:
            date_match = re.search(r'on\s+(.+)', decision_text, re.IGNORECASE)
            decision_date = date_match.group(1).strip() if date_match else None
            if status.lower() == 'accepted':
                accepted_date = decision_date
            elif status.lower() == 'rejected':
                rejected_date = decision_date
    
        # Initialize other fields
        start_term = None
        citizenship = None
        gpa = None
        gre_score = None
        gre_v = None
        gre_aw = None
        comments = None
    
        # Row 2: Additional details (if exists)
        if i + 1 < len(rows):
            row2 = rows[i + 1]
            # Row 2 has colspan and contains badges/chips with additional info
            if row2.find('td', colspan=True):
                details_text = row2.get_text()
            
                # Extract term (e.g., "Fall 2026")
                term_match = re.search(r'(Fall|Spring|Summer|Winter)\s+\d{4}', details_text)
                start_term = term_match.group(0) if term_match else None
            
                # Extract citizenship
                if 'International' in details_text:
                    citizenship = 'International'
                elif 'American' in details_text or 'Domestic' in details_text:
                    citizenship = 'American'
            
                # Extract GPA
                gpa_match = re.search(r'GPA\s+([\d\.]+)', details_text)
                gpa = gpa_match.group(1) if gpa_match else None
            
                # Extract GRE scores
                gre_match = re.search(r'GRE\s+(?:General\s+)?(\d+)', details_text)
                gre_score = gre_match.group(1) if gre_match else None
            
                gre_v_match = re.search(r'GRE\s+V\s*(\d+)', details_text)
                gre_v = gre_v_match.group(1) if gre_v_match else None
            
                gre_aw_match = re.search(r'(?:GRE\s+)?AW\s+([\d\.]+)', details_text)
                gre_aw = gre_aw_match.group(1) if gre_aw_match else None
            
                # Look for comments - text that's not part of standard badges
                comments = _clean_comment_text(details_text)
            
                i += 2  # Skip both rows
            else:
                i += 1  # Only skip row 1
        else:
            i += 1
    
        # Find the link to the individual result page for comments
        result_link = None
        if len(cells) > 4:
            link_tag = cells[4].find('a', href=True)
            if link_tag:
                result_link = link_tag['href']
                if not result_link.startswith('http'):
                    result_link = urlparse.urljoin(source_url, result_link)

        # Prefer richer comments from the individual result page if available
        if result_link:
            rich_comments = _extract_comments_from_result_page(result_link)
            if rich_comments:
                comments = rich_comments
    
        entry = {
            "program_name": program,
            "university": university,
            "comments": comments,
            "date_posted": date_posted,
            "url": result_link or source_url,
            "applicant_status": status,
            "accepted_date": accepted_date,
            "rejected_date": rejected_date,
            "start_term": start_term,
            "citizenship": citizenship,
            "gre_score": gre_score,
            "gre_v": gre_v,
            "gre_aw": gre_aw,
            "degree": degree,
            "gpa": gpa
        }
        entries.append(entry)

    return entries

def _find_post_links(html: str, base_url: str) -> List[str]:
    """Find survey links from the base page."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue
        if "/survey" in href:
            links.add(urlparse.urljoin(base_url, href))

    base_survey = urlparse.urljoin(base_url, "/survey/")
    ordered = [base_survey]
    for link in sorted(links):
        if link != base_survey:
            ordered.append(link)

    # de-dup preserve order
    seen = set()
    result = []
    for link in ordered:
        if link and link not in seen:
            seen.add(link)
            result.append(link)

    return result


def scrape_data(base_url: str = DEFAULT_BASE, limit: int = 50) -> List[Dict[str, Optional[str]]]:
    """Fetch entries from the base survey URL up to limit. Parse each page to extract multiple entries."""
    html = _fetch_url(base_url)
    if not html:
        return []

    links = _find_post_links(html, base_url)
    print(f"[scrape] found {len(links)} candidate links to process")

    results = []
    pages_processed = 0

    for link in links:
        if len(results) >= limit:
            break

        pages_processed += 1
        print(f"[scrape] page {pages_processed}: fetching {link}")
        page_html = _fetch_url(link)
        if not page_html:
            continue

        entries = _extract_entries_from_page(page_html, link)
        print(f"[scrape] extracted {len(entries)} entries from page")

        for entry in entries:
            if len(results) >= limit:
                break
            results.append(entry)

    print(f"[scrape] collected {len(results)} total entries from {pages_processed} pages")
    return results


def save_data(data: List[Dict[str, Optional[str]]], output_path: str = JSON_OUTPUT) -> None:
    """Save data (list of dicts) to JSON file."""
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(f"[save] wrote {len(data)} entries to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape The Grad Cafe")
    parser.add_argument("--base", help="Base URL to scrape", default=DEFAULT_BASE)
    parser.add_argument("--limit", help="Max number of posts to fetch", type=int, default=20)
    parser.add_argument("--out", help="Output JSON file", default=JSON_OUTPUT)
    args = parser.parse_args()

    data = scrape_data(base_url=args.base, limit=args.limit)
    save_data(data, args.out)
    print("Done.")
