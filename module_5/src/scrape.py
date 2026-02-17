#!/usr/bin/env python3
"""Web scraper for The GradCafe graduate school application results.

This module implements a web scraper that extracts graduate school application
data from The GradCafe website (thegradcafe.com). It parses HTML tables to
extract structured information about application outcomes, test scores, and
applicant demographics.

The scraper:
    - Respects rate limits with configurable delays
    - Handles pagination automatically
    - Extracts detailed information from both list and detail pages
    - Exports data in JSON format for further processing

Extracted Data Fields:
    - university: Name of the institution
    - program_name: Graduate program name
    - degree: Type of degree (PhD, Masters, etc.)
    - applicant_status: Decision outcome (Accepted, Rejected, etc.)
    - date_posted: When the result was posted
    - start_term: Intended start term (e.g., "Fall 2026")
    - citizenship: International or American
    - gpa: Grade Point Average
    - gre_score: GRE total score
    - gre_v: GRE verbal score
    - gre_aw: GRE analytical writing score
    - comments: Additional applicant notes

Example:
    Scrape 100 most recent entries::

        python scrape.py --limit 100 --out results.json

    Programmatic usage::

        from scrape import scrape_data, save_data

        data = scrape_data(limit=50)
        save_data(data, 'output.json')

Attributes:
    USER_AGENT (str): User agent string for HTTP requests
    DEFAULT_BASE (str): Base URL for The GradCafe
    JSON_OUTPUT (str): Default output filename

See Also:
    - :mod:`clean`: For cleaning scraped data
    - :mod:`load_data`: For loading scraped data into database
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


def _fetch_url(url: str, sleep: float = 0.1) -> Optional[str]:
    """Fetch URL content with rate limiting.

    Args:
        url: URL to fetch
        sleep: Delay in seconds after request (default: 0.1)

    Returns:
        HTML content as string, or None if request fails

    Note:
        Automatically adds User-Agent header to requests.
        Logs non-200 status codes to stdout.
    """
    resp = _http.request("GET", url, headers={"User-Agent": USER_AGENT})
    time.sleep(sleep)
    if resp.status != 200:
        print(f"[http] status {resp.status} for {url}")
        return None
    return resp.data.decode("utf-8", errors="replace")


def _extract_comments_from_result_page(result_url: str) -> Optional[str]:
    """Extract detailed comments from individual result page.

    Fetches an individual result page and extracts the Notes/Comments field,
    which often contains richer information than the summary view.

    Args:
        result_url: URL to individual result page

    Returns:
        Comment text if found, None otherwise

    Note:
        This makes an additional HTTP request per entry, so use judiciously
        based on rate limit and scraping volume requirements.
    """
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
    """Parse HTML table to extract application result entries.

    The GradCafe results table uses a 2-row format per entry:
        - Row 1: University, Program (with degree), Date posted, Decision
        - Row 2: Details (term, citizenship, GPA, GRE scores, comments)

    Args:
        html: HTML content of the results page
        source_url: URL of the page (for relative link resolution)

    Returns:
        List of dictionaries, each containing fields for one application result

    Note:
        Uses regular expressions to parse semi-structured data from badges
        and text labels. May need updates if GradCafe changes their HTML format.
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

def scrape_data(base_url: str = DEFAULT_BASE, limit: int = 50) -> List[Dict[str, Optional[str]]]:
    """Scrape application results from The GradCafe.

    Iterates through paginated results pages, extracting entries until
    the limit is reached or no more pages are available.

    Args:
        base_url: Base URL of The GradCafe (default: https://www.thegradcafe.com/)
        limit: Maximum number of entries to scrape (default: 50)

    Returns:
        List of dictionaries containing application result data

    Note:
        - Respects rate limits with delays between requests
        - Stops early if a page returns no entries
        - Logs progress to stdout

    Example:
        >>> results = scrape_data(limit=100)
        >>> print(f"Scraped {len(results)} entries")
    """
    results = []
    pages_processed = 0
    page_num = 1

    while len(results) < limit:
        # Build paginated URL
        if page_num == 1:
            page_url = urlparse.urljoin(base_url, "/survey/")
        else:
            page_url = urlparse.urljoin(base_url, f"/survey/?page={page_num}")

        pages_processed += 1
        print(f"[scrape] page {pages_processed}: fetching {page_url}")
        page_html = _fetch_url(page_url)
        if not page_html:
            print(f"[scrape] failed to fetch page {page_num}, stopping")
            break

        entries = _extract_entries_from_page(page_html, page_url)
        if not entries:
            print(f"[scrape] no entries found on page {page_num}, stopping")
            break

        print(f"[scrape] extracted {len(entries)} entries from page {page_num}")

        for entry in entries:
            if len(results) >= limit:
                break
            results.append(entry)

        page_num += 1

    print(f"[scrape] collected {len(results)} total entries from {pages_processed} pages")
    return results


def save_data(data: List[Dict[str, Optional[str]]], output_path: str = JSON_OUTPUT) -> None:
    """Save scraped data to JSON file.

    Args:
        data: List of entry dictionaries to save
        output_path: Path to output JSON file (default: applicant_data.json)

    Returns:
        None

    Note:
        Output is formatted with 2-space indentation and UTF-8 encoding
        for readability and international character support.
    """
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
