# Graduate School Applicant Database Analysis System

## Name & JHED ID
- **Name**: Brad Ballinger
- **JHED ID**: 4B16D1

## Overview

This project analyzes graduate school application data using PostgreSQL and Flask. It includes:
1. **load_data.py** - Loads JSON data into PostgreSQL database
2. **query_data.py** - Runs 11 analytical queries on the data
3. **app.py** - Flask web dashboard with JHU branding

## Quick Start

### Prerequisites

```bash
pip install psycopg2 flask reportlab beautifulsoup4 urllib3
```

Ensure PostgreSQL is running on localhost:5432

### Step 1: Load Data into Database

```bash
python load_data.py
```

This creates the `applicants` table and loads data from `llm_extend_applicant_data.json`.

### Step 2: Run Queries (Optional)

```bash
python query_data.py
```

Displays all 11 query results in the terminal.

### Step 3: Start Web Application

```bash
python app.py
```

Or use the startup script:
```bash
./run_webapp.sh
```

Then open http://127.0.0.1:5001 in your browser.

### Step 4: Pull New Data (Using Web Interface)

Once the web app is running, click the **"Pull Data"** button in the header to:
- Scrape the latest application data from GradCafe (up to 50 new entries)
- Automatically add new entries to the database
- Skip duplicate entries
- See real-time status updates

The scraping process typically takes 1-2 minutes.

### Step 5: Generate PDF Report (Optional)

```bash
python generate_report.py
```

Creates `query_results_report.pdf` with all query results.

## The 11 Queries

1. **Fall 2026 applications count** - Total applications for Fall 2026
2. **International student percentage** - Percent of international applicants
3. **Average test scores** - Mean GPA, GRE, GRE V, and GRE AW
4. **American students GPA** - Average GPA for American students (Fall 2026)
5. **Fall 2026 acceptance rate** - Percent accepted for Fall 2026
6. **Accepted students GPA** - Average GPA of accepted Fall 2026 applicants
7. **JHU CS Masters count** - Applications to JHU for CS Masters
8. **Elite university PhD acceptances** - 2026 PhD CS acceptances from Georgetown/MIT/Stanford/CMU
9. **LLM fields comparison** - Do LLM-generated fields change Query 8 results?
10. **Top 10 programs** - Most applied-to programs for Fall 2026
11. **PhD vs Masters** - Acceptance rate comparison by degree type

## Database Configuration

To change database settings, edit the connection parameters in both `load_data.py` (line 213) and `query_data.py` (line 7):

```python
conn_params = {
    'host': 'localhost',
    'port': 5432,
    'database': 'your_database_name',
    'user': 'your_username',
}
```

## Key Findings

- Masters programs: 64.92% acceptance rate
- PhD programs: 25.19% acceptance rate
- International students: 50.12% of applicants
- Fall 2026: 6,978 applications, 24.32% acceptance rate
- Most popular program: UW-Madison Mathematics (39 applications)

## Web Application Features

### Pull Data Button
The web interface includes a **"Pull Data"** button (bottom left of header) that:
- **Scrapes GradCafe**: Fetches up to 50 of the latest application entries
- **Automatic Import**: Converts and loads data directly into PostgreSQL
- **Duplicate Detection**: Skips entries already in the database
- **Real-time Feedback**: Shows progress and results (new entries added, duplicates skipped)
- **Auto-refresh Option**: Prompts to reload page if new data is added

This integrates the Module 2 scraping code (`scripts/scrape.py`) with the database system.

### Update Analysis Button
The web interface includes an **"Update Analysis"** button (top right of header) that:
- **Refreshes Analytics**: Reloads the page to display the most current data from the database
- **Smart Detection**: Prevents refresh if a data pull is currently running
- **User Notifications**: Alerts users if they try to update during an active data pull
- **Instant Update**: Quickly refreshes all queries and charts with latest database state

Use this button after manually adding data or to see the latest analytics without pulling new data from GradCafe.

## Project Files

```
module_3/
├── load_data.py              # Data loader
├── query_data.py             # Query runner
├── app.py                    # Flask web app (includes /pull-data endpoint)
├── generate_report.py        # PDF generator
├── templates/index.html      # Web template (with Pull Data button)
├── static/css/style.css      # Stylesheet (with button styling)
├── scripts/
│   ├── scrape.py            # GradCafe scraper (from Module 2)
│   └── clean.py             # Data cleaning utilities
└── llm_extend_applicant_data.json  # Initial data
```

## Troubleshooting

**Port 5000 in use?** App uses port 5001, or edit `app.py` to change port.

**Database connection error?** Verify PostgreSQL is running and connection parameters are correct.

**Data file not found?** Ensure `llm_extend_applicant_data.json` is in the current directory.

---

**Johns Hopkins University - Modern Python Course**
