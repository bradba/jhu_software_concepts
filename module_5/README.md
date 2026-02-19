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

**1. Install Dependencies:**
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install psycopg[binary] flask reportlab beautifulsoup4 urllib3
```

**2. Configure Database Connection:**

Create your `.env` file from the template:
```bash
cp .env.example .env
```

Edit `.env` with your database credentials (see [Database Configuration](#database-configuration) section for details):
```bash
# Edit with your database credentials
nano .env
```

**3. Ensure PostgreSQL is running** on localhost:5432

See [Database Security - Least-Privilege User Setup](#database-security---least-privilege-user-setup) for creating a secure database user.

### Fresh Install (Complete Setup from Scratch)

This section shows how to set up the entire project in a brand new environment using either **pip** (traditional) or **uv** (modern/faster).

#### Method 1: Fresh Install with pip (Traditional)

```bash
# Clone or download the project
cd module_5/

# Create a fresh virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Option A: Install from requirements.txt (all dependencies)
pip install -r requirements.txt

# Option B: Install as editable package (recommended for development)
pip install -e .[dev,docs]

# Configure database credentials
cp .env.example .env
nano .env  # Edit with your database settings

# Verify installation
python -c "import flask; import psycopg; print('✓ All dependencies installed')"

# Load initial data
python src/load_data.py

# Run the Flask web application
python src/app.py
```

#### Method 2: Fresh Install with uv (Faster Alternative)

[uv](https://github.com/astral-sh/uv) is a blazingly fast Python package installer written in Rust—up to 10-100x faster than pip.

```bash
# Clone or download the project
cd module_5/

# Install uv (if not already installed)
pip install uv
# Or on macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment with uv
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Option A: Install from requirements.txt
uv pip install -r requirements.txt

# Option B: Install as editable package (faster resolution)
uv pip install -e .[dev,docs]

# Configure database credentials
cp .env.example .env
nano .env  # Edit with your database settings

# Verify installation
python -c "import flask; import psycopg; print('✓ All dependencies installed')"

# Load initial data
python src/load_data.py

# Run the Flask web application
python src/app.py
```

#### Comparison: pip vs uv

| Feature | pip | uv |
|---------|-----|-----|
| **Installation Speed** | Baseline | 10-100x faster |
| **Dependency Resolution** | Can be slow on complex projects | Parallel resolution, extremely fast |
| **Compatibility** | Standard Python tool | Drop-in replacement for pip |
| **Cache** | Local cache | Global cache + optimizations |
| **Best For** | Standard workflows, CI/CD | Development, large dependency trees |

**When to use each:**
- **Use pip:** Standard installations, maximum compatibility, CI/CD pipelines
- **Use uv:** Local development, faster iteration, large projects with many dependencies

Both methods produce identical results—uv is simply faster at resolving and installing the same packages.

### Using Convenience Scripts (Recommended)

The project includes shell scripts that handle environment variable setup automatically:

```bash
# Step 1: Load data into database
./scripts/run_load_data.sh

# Step 2: Run queries (optional)
./scripts/run_queries.sh

# Step 3: Start the web application
./scripts/run_app.sh
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
./scripts/run_app.sh
# or
python src/load_data.py
```

### Using .env File (Recommended for Local Development)

**⚠️ SECURITY WARNING:** Never commit `.env` files to version control. They contain real credentials and are automatically excluded by `.gitignore`.

#### Quick Start

1. **Copy the template** - [`.env.example`](.env.example) is a safe template file (committed to git):
   ```bash
   cp .env.example .env
   ```

2. **Edit with your credentials** - Replace placeholder values in `.env`:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Configure database connection** - Choose one of two formats:

   **Option A: CONNECTION_URL (single line):**
   ```bash
   DATABASE_URL=postgresql://gradcafe_app_user:your_password@localhost:5432/your_db
   ```

   **Option B: Individual variables (more readable):**
   ```bash
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USER=gradcafe_app_user
   DB_PASSWORD=your_secure_password_here
   ```

4. **Load environment variables** before running the app:
   ```bash
   # Export all variables from .env
   export $(cat .env | xargs)

   # Then run the application
   python src/app.py
   ```

   Or use the convenience scripts which handle this automatically:
   ```bash
   ./scripts/run_app.sh
   ```

#### What Goes in Each File?

| File | Purpose | Committed to Git? | Contents |
|------|---------|-------------------|----------|
| `.env.example` | Template with placeholder values | ✅ Yes (safe) | `DB_USER=gradcafe_app_user` |
| `.env` | Your actual credentials | ❌ **NO** (in .gitignore) | `DB_PASSWORD=MyRealPassword123!` |

**Note:** The application reads environment variables directly from the shell environment. The `.env` file is just a convenient way to store them locally. You must manually export the variables before running Python (or use scripts that do this automatically).

For production deployments, set environment variables directly in your hosting platform (Heroku, AWS, etc.) rather than using `.env` files.

### Default Configuration

If no environment variables are set, the application uses these defaults:
- **Host**: localhost
- **Port**: 5432
- **Database**: bradleyballinger
- **User**: bradleyballinger
- **Password**: (empty)
- **LLM API URL**: http://localhost:8000/standardize

## Documentation

API documentation is automatically generated from code docstrings using Sphinx autodoc.

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
- **API Reference**: Complete autodoc for all modules (app, scrape, clean, load_data, query_data)
- **Function Signatures**: Parameters, return types, and descriptions
- **Module Index**: Searchable index of all functions and classes

### Viewing Documentation

After building, open `docs/_build/html/index.html` in your browser to view the API documentation.

## Running Tests

The project includes a comprehensive test suite with 100% code coverage (176 tests).

### Using Test Script (Recommended)

```bash
# Run all tests
./scripts/run_tests.sh

# Run with coverage report
./scripts/run_tests.sh coverage

# Run specific test categories
./scripts/run_tests.sh integration  # Integration tests only
./scripts/run_tests.sh unit        # Unit tests only
./scripts/run_tests.sh db          # Database tests
./scripts/run_tests.sh buttons     # Flask endpoint tests
./scripts/run_tests.sh verbose     # Verbose output
./scripts/run_tests.sh quick       # Quick run without coverage

# Show all options
./scripts/run_tests.sh help
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
module_5/
├── README.md                           # This file
├── setup.py                            # Package configuration (makes project installable)
├── requirements.txt                    # Python dependencies (runtime + dev + docs)
├── .gitignore                          # Git ignore file (excludes .env)
├── .env.example                        # SAFE template - copy to .env and configure
├── .env                                # YOUR CREDENTIALS - never commit (gitignored)
├── dependency.svg                      # Module dependency graph (pydeps + Graphviz)
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
│   ├── api.rst                         # API reference
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
└── tests/                              # Test suite (176 tests, 100% coverage)
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

## Python Packaging & Reproducible Environments

### Why Packaging Matters

This project includes a [`setup.py`](setup.py) file that makes it installable as a proper Python package, providing several critical benefits for development, testing, and deployment:

**1. Consistent Import Behavior**
Without packaging, Python imports can behave differently depending on how the code is run (direct execution vs. module import vs. test runner). Installing the package with `pip install -e .` ensures imports work consistently everywhere—local development, CI/CD pipelines, and production environments. This eliminates "it works on my machine" issues caused by `sys.path` manipulation.

**2. Dependency Management**
The `setup.py` declares all runtime dependencies (`install_requires`) and optional development dependencies (`extras_require`). This enables tools like `pip`, `uv`, and `poetry` to automatically resolve and install the complete dependency tree, ensuring reproducible environments across different machines and time periods.

**3. Editable Installs for Development**
Running `pip install -e .` creates an editable install where changes to source files immediately reflect in the installed package—no reinstall needed. This dramatically improves the development workflow while maintaining proper import paths and package structure.

**4. Distribution & Deployment**
Packaging enables multiple distribution methods: uploading to PyPI for public sharing, building wheel files (`.whl`) for efficient installation, or installing directly from version control systems. This standardization makes the project portable and easier to deploy across different environments (development, staging, production).

**5. Tool Integration**
Modern Python tools like `uv` (ultra-fast package installer), `tox` (testing automation), and `setuptools-scm` (version management from git tags) all expect properly packaged projects. Packaging unlocks this ecosystem of productivity tools and ensures the project follows Python community best practices.

### Installing the Package

**Development installation (editable mode):**
```bash
# Install package in editable mode with all development tools
pip install -e .[dev,docs]
```

**Production installation:**
```bash
# Install package with only runtime dependencies
pip install .
```

**Using uv (faster alternative to pip):**
```bash
# Install uv if not already installed
pip install uv

# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .[dev,docs]
```

### Requirements Files

| File | Purpose | Used By |
|------|---------|---------|
| [`requirements.txt`](requirements.txt) | All dependencies (runtime + dev + docs) | Direct `pip install -r` workflow |
| [`setup.py`](setup.py) | Package metadata + dependencies | `pip install -e .`, distribution, uv |

The project supports both workflows: traditional `pip install -r requirements.txt` and modern `pip install -e .` for package-based development.

## Code Quality — Pylint

Pylint is used to enforce code style and catch errors across all Python source and test files.

**Run Pylint:**

```bash
.venv/bin/pylint src/ tests/
```

**Configuration** is in [`.pylintrc`](.pylintrc) at the project root. Key settings:
- `init-hook` adds `src/` to `sys.path` so local imports resolve correctly
- `max-line-length = 120`
- Design limits raised to accommodate data pipeline functions (e.g., `max-locals = 50`)

**Expected result:**

```
Your code has been rated at 10.00/10
```

---

**Johns Hopkins University - Modern Python Course**
