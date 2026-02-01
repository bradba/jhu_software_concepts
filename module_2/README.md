# The Grad Cafe Scraper ✅

**What this project provides**

- scrape.py: a polite scraper for https://www.thegradcafe.com/ that:
  - uses urllib3 for HTTP requests and urllib.parse for URL management
  - parses page content with BeautifulSoup (built-in html.parser)
  - exposes two public functions:
    - scrape_data(base_url=None, limit=100) -> list[dict]
    - save_data(data, output_path='applicant_data.json') -> None
- clean.py: utilities to normalize and sanitize scraped data:
  - load_data(path) -> list[dict]
  - clean_data(data, missing_value=None) -> list[dict]
  - save_data(data, path) -> None

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

Run a quick scrape and save results:

  python3 scrape.py --limit 10 --out applicant_data.json

Clean the scraped data (strip HTML, normalize missing values):

  python3 -c "from clean import load_data, clean_data, save_data; data = load_data('applicant_data.json'); cleaned = clean_data(data); save_data(cleaned, 'applicant_data_clean.json')"

What happens when you run it:
- The scraper will collect candidate entry links and parse each entry; results will be stored in applicant_data.json.
- The cleaner removes HTML remnants and normalizes missing fields to a consistent value (default: None).

## Notes & Limitations 💡
- The Grad Cafe content is user-submitted and free-form; the parser uses heuristics and will not be 100% accurate on all posts.
- The scraper is intentionally conservative (sleeps between requests). Respect rate limits and terms of use.

## License & Ethics ⚠️
- Only use this tool according to The Grad Cafe's terms of service.
- The scraper is intentionally conservative (sleeps between requests). Respect rate limits and terms of use.

---

**Author**
- Brad Ballinger (JHED ID: 4B16D1)