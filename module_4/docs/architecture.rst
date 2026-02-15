System Architecture
===================

This document describes the architecture and design of the Graduate School Applicant Database Analysis System.

Overview
--------

The application follows a three-tier architecture:

1. **Web Layer** (Presentation): Flask web application
2. **ETL Layer** (Business Logic): Data scraping, cleaning, and loading
3. **Database Layer** (Persistence): PostgreSQL database

.. code-block:: text

   ┌─────────────────────────────────────────────────────────┐
   │                     Web Layer                           │
   │  ┌─────────────────────────────────────────────────┐   │
   │  │  Flask Application (app.py)                     │   │
   │  │  - Web dashboard with JHU branding              │   │
   │  │  - REST API endpoints (/pull-data, /update)     │   │
   │  │  - Real-time scraping integration               │   │
   │  └─────────────────────────────────────────────────┘   │
   └─────────────────────────────────────────────────────────┘
                            ↓
   ┌─────────────────────────────────────────────────────────┐
   │                     ETL Layer                           │
   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
   │  │  Scraping    │  │  Cleaning    │  │  Loading     │ │
   │  │  (scrape.py) │→ │  (clean.py)  │→ │(load_data.py)│ │
   │  └──────────────┘  └──────────────┘  └──────────────┘ │
   └─────────────────────────────────────────────────────────┘
                            ↓
   ┌─────────────────────────────────────────────────────────┐
   │                   Database Layer                        │
   │  ┌─────────────────────────────────────────────────┐   │
   │  │  PostgreSQL Database                            │   │
   │  │  - applicants table (main data)                 │   │
   │  │  - Optimized indexes for queries                │   │
   │  │  - Query functions (query_data.py)              │   │
   │  └─────────────────────────────────────────────────┘   │
   └─────────────────────────────────────────────────────────┘

Web Layer
---------

**Module:** ``app.py``

The web layer is responsible for:

* **User Interface**: Serving HTML templates with JHU branding
* **API Endpoints**: RESTful endpoints for data operations
* **Query Orchestration**: Executing database queries and formatting results
* **Concurrency Control**: Managing busy states for long-running operations

Key Components
~~~~~~~~~~~~~~

**Routes:**

* ``GET /`` - Main dashboard displaying all query results
* ``POST /pull-data`` - Scrape new data and insert into database
* ``POST /update-analysis`` - Update LLM-generated analysis fields

**Features:**

* Thread-safe busy state management for concurrent requests
* Real-time progress feedback for scraping operations
* Automatic duplicate detection and skipping
* Error handling with user-friendly messages

**Dependencies:**

* Flask (web framework)
* query_data (database queries)
* scrape.py (via subprocess)
* load_data (data parsing utilities)

ETL Layer
---------

The ETL (Extract, Transform, Load) layer consists of three main modules:

Scraping Module (scrape.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Responsibilities:**

* Extract application data from GradCafe website
* Parse HTML tables and extract structured data
* Handle pagination and rate limiting
* Extract rich comments from detail pages

**Key Functions:**

* ``scrape_data(limit, page_offset, user_agent, search_url)`` - Main scraping function
* ``_fetch_url(url, user_agent)`` - HTTP request with retry logic
* ``_extract_entries_from_page(html, base_url)`` - Parse HTML table rows
* ``_extract_comments_from_result_page(url)`` - Extract detailed comments

**Output Format:**

JSON lines format with fields:

.. code-block:: python

   {
       "url": "https://www.thegradcafe.com/survey/result/123456",
       "university": "Stanford University",
       "program_name": "Computer Science PhD",
       "comments": "Great funding package...",
       "date_posted": "February 01, 2026",
       "applicant_status": "Accepted",
       "start_term": "Fall 2026",
       "citizenship": "International",
       "gpa": "3.9",
       "gre_score": "330",
       "gre_v": "168",
       "gre_aw": "5.0",
       "degree": "PhD"
   }

Cleaning Module (clean.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Responsibilities:**

* Remove HTML tags and entities from scraped data
* Normalize missing values to consistent format
* Clean comment text by removing boilerplate tokens
* Standardize university and program names via LLM API

**Key Functions:**

* ``load_data(path)`` - Load JSON data from file
* ``clean_data(data, missing_value)`` - Clean all records
* ``_clean_comment_text(text)`` - Remove badges and boilerplate
* ``_standardize_with_llm(data, api_url)`` - LLM standardization

**Data Transformations:**

1. HTML stripping: ``<p>Stanford University</p>`` → ``Stanford University``
2. Whitespace normalization: ``Test   Multiple    Spaces`` → ``Test Multiple Spaces``
3. Comment cleaning: Remove terms like ``Fall 2026``, ``International``, ``GPA 3.8``
4. Text truncation: Limit comments to 500 characters

Loading Module (load_data.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Responsibilities:**

* Parse JSON lines data format
* Extract p_id from GradCafe URLs
* Convert scraped format to database schema
* Batch insert records efficiently (1000 records per batch)
* Handle duplicates with ON CONFLICT clause

**Key Functions:**

* ``load_json_data(json_file_path, conn)`` - Main loading function
* ``parse_gpa(gpa_str)`` - Extract numeric GPA values
* ``parse_gre_score(gre_str)`` - Extract numeric GRE scores
* ``parse_date(date_str)`` - Convert date strings to date objects
* ``extract_p_id_from_url(url)`` - Extract unique identifier from URL

**Database Schema:**

.. code-block:: sql

   CREATE TABLE applicants (
       p_id INTEGER PRIMARY KEY,
       program TEXT,
       comments TEXT,
       date_added DATE,
       url TEXT,
       status TEXT,
       term TEXT,
       us_or_international TEXT,
       gpa NUMERIC(3,2),
       gre NUMERIC(5,2),
       gre_v NUMERIC(5,2),
       gre_aw NUMERIC(3,2),
       degree TEXT,
       llm_generated_program TEXT,
       llm_generated_university TEXT
   );

Database Layer
--------------

**Module:** ``query_data.py``

The database layer is responsible for:

* **Connection Management**: PostgreSQL connection pooling
* **Query Execution**: 11 analytical queries
* **Result Formatting**: Converting database results to displayable format

Database Queries
~~~~~~~~~~~~~~~~

The system implements 11 analytical queries:

1. **Fall 2026 Applications**: Count of Fall 2026 applicants
2. **International Percentage**: Percentage of international students
3. **Average Scores**: Mean GPA, GRE, GRE V, and GRE AW scores
4. **American Student GPA**: Average GPA for American students (Fall 2026)
5. **Acceptance Rate**: Percentage accepted for Fall 2026
6. **Accepted Student GPA**: Average GPA of accepted Fall 2026 applicants
7. **JHU CS Masters**: Count of JHU CS Masters applications
8. **Elite PhD Acceptances**: 2026 PhD CS acceptances from Georgetown/MIT/Stanford/CMU
9. **LLM Field Comparison**: Compare LLM-generated vs original fields
10. **Top 10 Programs**: Most applied-to programs for Fall 2026
11. **PhD vs Masters**: Acceptance rate comparison by degree type

Query Optimization
~~~~~~~~~~~~~~~~~~

* Index on ``term`` for fast filtering
* Index on ``status`` for acceptance rate queries
* Efficient aggregation using PostgreSQL built-in functions
* Minimized database round-trips

Connection Management
~~~~~~~~~~~~~~~~~~~~~

**Environment-based Configuration:**

The system supports flexible database configuration:

.. code-block:: python

   # Option 1: DATABASE_URL
   database_url = os.environ.get('DATABASE_URL')
   # postgresql://user:pass@host:port/db

   # Option 2: Individual variables
   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

**Connection Pattern:**

.. code-block:: python

   def get_connection():
       """Create and return a database connection."""
       # Parse environment variables
       # Return psycopg2 connection
       return psycopg2.connect(**conn_params)

Data Flow
---------

Complete Data Flow Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **User clicks "Pull Data" button** in web interface
2. **Flask endpoint** ``/pull-data`` is triggered
3. **Subprocess** launches ``scrape.py`` to fetch new data
4. **Scraper** extracts 50 entries from GradCafe and saves to JSON
5. **Flask app** reads JSON file
6. **Data parsing** converts each entry to database format
7. **Database insert** uses ``ON CONFLICT DO NOTHING`` for duplicates
8. **Response** returns count of inserted/skipped records
9. **Frontend** displays results and prompts page refresh

Error Handling
--------------

The system implements comprehensive error handling at each layer:

**Web Layer:**

* 409 Conflict for busy state (operation already running)
* 500 Internal Server Error for unexpected failures
* Graceful degradation for database connection issues

**ETL Layer:**

* Retry logic for network requests (scraping)
* Graceful skipping of malformed records
* Logging of parsing errors without stopping pipeline
* Timeout handling for LLM API calls

**Database Layer:**

* Connection pooling to handle temporary disconnects
* Transaction rollback on error
* Duplicate key handling via ON CONFLICT clause

Security Considerations
-----------------------

**Environment Variables:**

* Database credentials never hardcoded
* Support for ``.env`` files (not committed to git)
* Separate test database configuration

**Input Validation:**

* URL validation before scraping
* SQL injection prevention via parameterized queries
* HTML sanitization of scraped content

**Rate Limiting:**

* Sleep delays between scrape requests
* Configurable scraping limits
* User-agent header configuration

Scalability
-----------

**Current Scale:**

* ~26,000 records in initial dataset
* 50 new records per scraping operation
* Sub-second query response times

**Scaling Strategies:**

* Batch insertions (1000 records per batch)
* Connection pooling for concurrent requests
* Indexed queries for fast filtering
* Async scraping for parallel data collection

Performance Metrics
-------------------

**Typical Performance:**

* Data loading: ~5 seconds for 1000 records
* Scraping: ~2 minutes for 50 records
* Query execution: <100ms per query
* Page load: <500ms including all queries

Next Steps
----------

* See :doc:`api` for detailed function documentation
* See :doc:`testing` for testing architecture and conventions
