# The Grad Cafe Scraper ✅

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

## Notes & Limitations 💡

- **Parsing accuracy**: The Grad Cafe content is user-submitted and free-form; the parser uses heuristics and table-based extraction (2 rows per entry) for best accuracy.
- **Rate limiting**: The scraper is intentionally conservative with 0.1s delays between requests. Respect rate limits and The Grad Cafe's terms of service.
- **LLM standardization**: Optional AI-powered standardization requires a running Flask server with llama-cpp-python. For large datasets (50,000+ entries), expect this to take considerable time.
- **Resumption**: If the LLM standardization process is interrupted, rerunning with `--standardize` will detect existing progress and resume from the last checkpoint.

## License & Ethics ⚠️

- Only use this tool according to The Grad Cafe's terms of service.
- Respect request rate limits: the scraper uses 0.1s delays by default.
- Do not use for commercial purposes or to republish data without permission.

---

**Author**
- Brad Ballinger (JHED ID: 4B16D1)