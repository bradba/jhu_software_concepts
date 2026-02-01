# The Grad Cafe Scraper ✅

## Name & JHED ID
- **Name**: Brad Ballinger
- **JHED ID**: 4B16D1

## Module Info
- **Module**: Modern Python Software Concepts (EN.605.711)
- **Assignment**: Module 2 - Web Scraping & Data Cleaning Pipeline
- **Due Date**: February 1, 2026

## Approach

### Architecture Overview
This project implements a two-stage data processing pipeline:

1. **Web Scraper (scrape.py)**
   - **HTTP Client**: Uses `urllib3.PoolManager` for connection pooling and robust HTTP request handling
   - **Parsing Strategy**: BeautifulSoup with html.parser backend to extract data from HTML tables
   - **Table Structure**: The Grad Cafe displays 20 entries per page in an HTML table where each entry spans 2 rows:
     - Row 1: university, program_name, degree, date_posted, applicant_status
     - Row 2: start_term, citizenship, gpa, gre_score, gre_v, gre_aw, comments (truncated)
   - **Rich Comments**: Individual result pages are fetched to extract full "Notes" field from dt/dd elements
   - **Pagination**: Implements parameter-based pagination (?page=1, ?page=2, ...) to support scraping datasets of arbitrary size
   - **Rate Limiting**: 0.1s delay between requests to respect server load and terms of service
   - **Public API**:
     - `scrape_data(base_url, limit)`: Orchestrates pagination and returns list of cleaned dictionaries
     - `save_data(data, output_path)`: Writes JSON with 2-space indent and UTF-8 encoding

2. **Data Cleaning & Standardization (clean.py)**
   - **HTML Stripping**: Uses BeautifulSoup's `.get_text()` method with aggressive whitespace normalization (regex: `\s+` -> single space)
   - **Normalization Pipeline**:
     - `_strip_html()`: Remove HTML tags and entities
     - `_normalize_value()`: Handle None values and empty strings uniformly
     - `_clean_record()`: Apply normalization to all dictionary fields
   - **CLI Interface**: argparse-based CLI with flags:
     - `--input`: Source JSON file (default: applicant_data.json)
     - `--output`: Destination JSON file (default: applicant_data_clean.json)
     - `--api`: LLM API endpoint (default: http://localhost:8000/standardize)
     - `--standardize`: Enable optional LLM-based standardization
   - **LLM Integration**:
     - `_standardize_university_with_llm()`: Single-entry API call to Flask server
     - `_standardize_with_llm()`: Batch processor with checkpoint saves every 100 entries
     - **Resumption Logic**: Detects existing output file and skips entries that have `llm-generated-university` field
   - **Public API**:
     - `load_data(path)`: Load JSON array from file
     - `clean_data(data, missing_value)`: Remove HTML and normalize missing values
     - `save_data(data, path)`: Write JSON to file

3. **LLM Hosting Server (llm_hosting/app.py)**
   - **Model**: TinyLlama 1.1B Chat (Q4_K_M quantization) via `llama-cpp-python`
   - **Framework**: Flask with a single POST endpoint `/standardize`
   - **Input/Output**: Accepts JSON array of entries, returns array with added `llm-generated-university` and `llm-generated-program` fields
   - **Inference**: Implements a system prompt that instructs the model to standardize messy university/program names to canonical forms

### Data Structures
- **Primary format**: List of dictionaries (JSON-serializable)
- **Entry structure**: 15+ fields per entry (program_name, university, comments, dates, scores, citizenship, etc.)
- **Intermediate storage**: applicant_data.json (raw scraped), applicant_data_clean.json (cleaned+standardized)

### Algorithms & Key Decisions
1. **Table Row Pairing**: Each GradCafe entry spans 2 consecutive table rows; the scraper tracks row index modulo 2 to group related data
2. **Comment Enrichment**: After initial extraction, the scraper fetches individual result pages to retrieve complete "Notes" fields via BeautifulSoup's dt/dd extraction
3. **Checkpoint-Based Resumption**: Every 100 entries, standardization progress is flushed to disk; on restart, the script loads existing output and detects which entries have LLM fields to avoid re-processing
4. **Lazy API Connection**: HTTP client created once at module level (_http = urllib3.PoolManager()) for connection pooling efficiency

## Known Bugs

**None identified.** The scraper correctly:
- Extracts all 15+ fields from table rows and enriches comments with full notes
- Handles pagination without dropping entries
- Cleans HTML and normalizes missing values consistently
- Resumes LLM standardization without data loss or duplication

**What this project provides**

- **scrape.py**: a polite scraper for https://www.thegradcafe.com/ that:
  - uses urllib3 for HTTP requests with rate limiting (0.1s delay)
  - parses page content with BeautifulSoup (html.parser backend)
  - supports pagination (?page=1, ?page=2, ...) to scrape large datasets
  - exposes two public functions:
    - `scrape_data(base_url=None, limit=100)` -> list[dict]
    - `save_data(data, output_path='applicant_data.json')` -> None

- **clean.py**: utilities to normalize, sanitize, and standardize scraped data:
  - `load_data(path)` -> list[dict]
  - `clean_data(data, missing_value=None)` -> list[dict]
  - `save_data(data, path)` -> None
  - CLI interface with `--input`, `--output`, `--api`, and `--standardize` flags
  - Optional LLM-based standardization of university and program names via Flask API
  - Checkpoint-based resumption (saves progress every 100 entries)

**Data saved**
- Output JSON file: applicant_data.json
- Reasonable object keys include: program_name, university, comments, date_posted, url, applicant_status, accepted_date, rejected_date, start_term, citizenship, gre_score, gre_v, gre_aw, degree, gpa.

## Installation 🔧

1. Create and activate a virtualenv (recommended):

   python3 -m venv env
   source env/bin/activate

2. Install dependencies:

   pip install -r requirements.txt

## Usage ▶️

### Basic scraping (10 entries):

```bash
python3 scrape.py --limit 10 --out applicant_data.json
```

### Clean the scraped data (strip HTML, normalize missing values):

```bash
python3 clean.py --input applicant_data.json --output applicant_data_clean.json
```

### Clean and standardize university/program names using LLM:

```bash
# First, start the LLM hosting server in another terminal:
cd llm_hosting
python3 app.py --serve

# Then, run clean.py with standardization:
python3 clean.py --input applicant_data.json --output applicant_data_clean.json --standardize
```

The `--standardize` flag will:
- Call the Flask API at `http://localhost:8000/standardize` (customizable with `--api`)
- Add `llm-generated-university` and `llm-generated-program` fields to each entry
- Save checkpoint progress every 100 entries to allow resumption on failure

## Notes & Limitations

- **Parsing accuracy**: The Grad Cafe content is user-submitted and free-form; the parser uses heuristics and table-based extraction (2 rows per entry) for best accuracy.
- **Rate limiting**: The scraper is intentionally conservative with 0.1s delays between requests. Respect rate limits and The Grad Cafe's terms of service.
- **LLM standardization**: Optional AI-powered standardization requires a running Flask server with llama-cpp-python. For large datasets (50,000+ entries), expect this to take considerable time.
- **Resumption**: If the LLM standardization process is interrupted, rerunning with `--standardize` will detect existing progress and resume from the last checkpoint.

