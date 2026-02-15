# Graduate School Applicant Database Analysis System

## Name & JHED ID
- **Name**: Brad Ballinger
- **JHED ID**: 4B16D1

## Overview

This project analyzes graduate school application data using PostgreSQL and Flask. It includes:
1. **src/load_data.py** - Loads JSON data into PostgreSQL database
2. **src/query_data.py** - Runs 11 analytical queries on the data
3. **src/app.py** - Flask web dashboard with JHU branding

## Quick Start

### Prerequisites

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install psycopg[binary] flask reportlab beautifulsoup4 urllib3
```

**Ensure PostgreSQL is running** on localhost:5432

### Using Convenience Scripts (Recommended)

The project includes shell scripts that handle environment variable setup automatically:

```bash
# Step 1: Load data into database
./scripts/scripts/run_load_data.sh

# Step 2: Run queries (optional)
./scripts/scripts/run_queries.sh

# Step 3: Start the web application
./scripts/scripts/run_app.sh
```

These scripts use default environment variables and can be customized by setting environment variables before running.

### Manual Setup (Alternative)

If you prefer to run commands directly:

**Step 1: Load Data into Database**
```bash
python src/load_data.py
```

**Step 2: Run Queries (Optional)**
```bash
python src/query_data.py
```

**Step 3: Start Web Application**
```bash
python src/app.py
```

Then open http://127.0.0.1:5001 in your browser.

### Step 4: Pull New Data (Using Web Interface)

Once the web app is running, click the **"Pull Data"** button in the header to:
- Scrape the latest application data from GradCafe (up to 50 new entries)
- Automatically add new entries to the database
- Skip duplicate entries
- See real-time status updates

The scraping process typically takes 1-2 minutes.


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

The application supports flexible database configuration through environment variables.

### Using Environment Variables (Recommended)

**Option 1: DATABASE_URL** (PostgreSQL connection string)
```bash
export DATABASE_URL="postgresql://username:password@hostname:port/database"
python src/load_data.py
```

**Option 2: Individual Environment Variables**
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=your_database_name
export DB_USER=your_username
export DB_PASSWORD=your_password  # Optional
python src/load_data.py
```

### Using Setup Script

For convenience, you can create a setup script from the example:

```bash
cp scripts/setup_env_example.sh scripts/setup_env.sh
# Edit scripts/setup_env.sh with your database credentials
source scripts/setup_env.sh
```

Then run any command:
```bash
./scripts/scripts/run_app.sh
# or
python src/load_data.py
```

### Using .env File

Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

Example `.env` file:
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/mydb
# OR use individual variables:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=mydb
# DB_USER=myuser
# DB_PASSWORD=mypassword

# LLM API Configuration
LLM_API_URL=http://localhost:8000/standardize
```

**Note:** The application reads environment variables directly. If using a `.env` file, you'll need to load it with a tool like `python-dotenv` or manually export the variables before running the application.

### Default Configuration

If no environment variables are set, the application uses these defaults:
- **Host**: localhost
- **Port**: 5432
- **Database**: bradleyballinger
- **User**: bradleyballinger
- **Password**: (empty)
- **LLM API URL**: http://localhost:8000/standardize

## Documentation

Comprehensive Sphinx documentation is available covering setup, architecture, API reference, and testing.

### Building Documentation

```bash
# Install documentation dependencies
pip install sphinx sphinx-rtd-theme

# Build HTML documentation
cd docs
make html

# Open documentation in browser
open _build/html/index.html
```

The documentation includes:
- **Setup Guide**: Installation, environment variables, and quick start
- **Architecture**: System design, layers, and data flow
- **API Reference**: Complete autodoc for all modules and functions
- **Testing Guide**: How to run tests, use fixtures, and test markers

### Viewing Documentation

After building, open `docs/_build/html/index.html` in your browser to view the complete documentation.

## Running Tests

The project includes a comprehensive test suite with 100% code coverage (166 tests).

### Using Test Script (Recommended)

```bash
# Run all tests
./scripts/scripts/run_tests.sh

# Run with coverage report
./scripts/scripts/run_tests.sh coverage

# Run specific test categories
./scripts/scripts/run_tests.sh integration  # Integration tests only
./scripts/scripts/run_tests.sh unit        # Unit tests only
./scripts/scripts/run_tests.sh db          # Database tests
./scripts/scripts/run_tests.sh buttons     # Flask endpoint tests
./scripts/scripts/run_tests.sh verbose     # Verbose output
./scripts/scripts/run_tests.sh quick       # Quick run without coverage

# Show all options
./scripts/scripts/run_tests.sh help
```

### Using pytest Directly

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test categories
pytest tests/ -m db          # Database tests
pytest tests/ -m integration # Integration tests
pytest tests/ -m buttons     # Flask endpoint tests

# Run specific test file
pytest tests/test_query_data_unit.py -v
```

### Test Database Configuration

For integration tests that use a real PostgreSQL database, you can configure the test database using environment variables:

```bash
# Use separate test database
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/test_db"
pytest tests/test_integration_end_to_end.py

# Or use same DB_* variables as the main application
export DB_NAME=test_database
pytest tests/
```

If not specified, tests will use the default database configuration.

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

This integrates the Module 2 scraping code (`src/scripts/scrape.py`) with the database system.

### Update Analysis Button
The web interface includes an **"Update Analysis"** button (top right of header) that:
- **Refreshes Analytics**: Reloads the page to display the most current data from the database
- **Smart Detection**: Prevents refresh if a data pull is currently running
- **User Notifications**: Alerts users if they try to update during an active data pull
- **Instant Update**: Quickly refreshes all queries and charts with latest database state

Use this button after manually adding data or to see the latest analytics without pulling new data from GradCafe.

## Shell Scripts

The project includes convenient shell scripts to simplify running the application and tests:

| Script | Description | Usage |
|--------|-------------|-------|
| `scripts/run_app.sh` | Start the Flask web application | `./scripts/run_app.sh` |
| `scripts/run_load_data.sh` | Load data into the database | `./scripts/run_load_data.sh` |
| `scripts/run_queries.sh` | Run all database queries | `./scripts/run_queries.sh` |
| `scripts/run_tests.sh` | Run the test suite with options | `./scripts/run_tests.sh [option]` |
| `scripts/setup_env_example.sh` | Example environment setup | `cp scripts/setup_env_example.sh scripts/setup_env.sh && source scripts/setup_env.sh` |

**Test Script Options:**
- `./scripts/run_tests.sh` - Run all tests
- `./scripts/run_tests.sh coverage` - Run with coverage report
- `./scripts/run_tests.sh integration` - Run integration tests only
- `./scripts/run_tests.sh unit` - Run unit tests only
- `./scripts/run_tests.sh help` - Show all options

## Project Structure

```
module_4/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Git ignore file
├── .env.example                        # Example environment configuration
├── llm_extend_applicant_data.json      # Initial data (26MB)
├── scripts/                            # Shell scripts directory
│   ├── run_app.sh                      # Script to run Flask application
│   ├── run_load_data.sh                # Script to load data into database
│   ├── run_queries.sh                  # Script to run database queries
│   ├── run_tests.sh                    # Script to run test suite
│   └── setup_env_example.sh            # Example environment setup script
├── docs/                               # Sphinx documentation
│   ├── Makefile                        # Documentation build file
│   ├── conf.py                         # Sphinx configuration
│   ├── index.rst                       # Documentation home page
│   ├── setup.rst                       # Setup guide
│   ├── architecture.rst                # Architecture documentation
│   ├── api.rst                         # API reference
│   └── testing.rst                     # Testing guide
├── src/                                # Source code directory
│   ├── __init__.py                     # Package initialization
│   ├── app.py                          # Flask web app (includes /pull-data endpoint)
│   ├── load_data.py                    # Data loader
│   ├── query_data.py                   # Query runner
│   ├── clean.py                        # Data cleaning utilities
│   ├── scrape.py                       # GradCafe scraper
│   ├── static/                         # Static web assets
│   │   └── css/
│   │       └── style.css               # JHU-themed stylesheet
│   └── templates/                      # HTML templates
│       └── index.html                  # Web template (with control panel)
└── tests/                              # Test suite (166 tests, 100% coverage)
    ├── test_analysis_format.py         # Analysis format tests
    ├── test_app_errors.py              # Flask endpoint error tests
    ├── test_buttons.py                 # Button functionality tests
    ├── test_clean_unit.py              # Data cleaning unit tests
    ├── test_db_insert.py               # Database insertion tests
    ├── test_flask_page.py              # Flask page rendering tests
    ├── test_integration_end_to_end.py  # End-to-end integration tests
    ├── test_load_data_unit.py          # Data loading unit tests
    ├── test_query_data_unit.py         # Query function unit tests
    └── test_scrape_unit.py             # Scraper unit tests
```
---

**Johns Hopkins University - Modern Python Course**
