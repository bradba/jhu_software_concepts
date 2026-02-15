API Reference
=============

This section provides detailed API documentation for all modules in the system.

Web Application
---------------

.. automodule:: app
   :members:
   :undoc-members:
   :show-inheritance:

**Key Routes:**

.. py:function:: index()

   Main dashboard route that displays all query results.

   :returns: Rendered HTML template with query results
   :rtype: str

.. py:function:: pull_data()

   Scrape new data from GradCafe and insert into database.

   **Workflow:**

   1. Check if system is busy
   2. Run scraper subprocess
   3. Load scraped JSON data
   4. Parse and insert records into database
   5. Return status and counts

   :returns: JSON response with status, inserted count, and skipped count
   :rtype: flask.Response
   :status: 200 OK on success
   :status: 409 Conflict if busy
   :status: 500 Internal Server Error on failure

   **Response Format:**

   .. code-block:: json

      {
        "status": "success",
        "message": "Successfully added 42 new entries to database",
        "inserted": 42,
        "skipped": 8,
        "timestamp": "2026-02-09T15:30:45.123456"
      }

.. py:function:: update_analysis()

   Update LLM-generated analysis fields for applicants.

   :returns: JSON response with status and message
   :rtype: flask.Response
   :status: 200 OK on success
   :status: 409 Conflict if busy
   :status: 500 Internal Server Error on failure

Data Scraping
-------------

.. automodule:: scrape
   :members:
   :undoc-members:
   :show-inheritance:

**Main Functions:**

.. autofunction:: scrape.scrape_data

   Scrape graduate school application data from GradCafe.

   :param int limit: Maximum number of entries to scrape
   :param int page_offset: Starting page number (default: 1)
   :param str user_agent: User agent string for HTTP requests
   :param str search_url: Base URL for GradCafe search
   :returns: List of entry dictionaries
   :rtype: List[Dict[str, Any]]

   **Entry Format:**

   .. code-block:: python

      {
          "url": str,
          "university": str,
          "program_name": str,
          "comments": Optional[str],
          "date_posted": str,
          "applicant_status": str,  # "Accepted", "Rejected", "Waitlist"
          "start_term": str,  # "Fall 2026", "Spring 2026", etc.
          "citizenship": str,  # "International", "American"
          "gpa": Optional[str],
          "gre_score": Optional[str],
          "gre_v": Optional[str],
          "gre_aw": Optional[str],
          "degree": str  # "PhD", "Masters", "Other"
      }

.. autofunction:: scrape.save_data

   Save scraped data to JSON file.

   :param List[Dict] data: List of entry dictionaries
   :param str path: Output file path
   :rtype: None

Data Cleaning
-------------

.. automodule:: clean
   :members:
   :undoc-members:
   :show-inheritance:

**Main Functions:**

.. autofunction:: clean.load_data

   Load application data from a JSON file.

   :param str path: Path to JSON file
   :returns: List of records
   :rtype: List[Dict[str, Any]]
   :raises ValueError: If data is not a list

.. autofunction:: clean.clean_data

   Convert data into a structured, cleaned format.

   - Strips HTML from all string fields
   - Normalizes missing/empty values to a consistent format

   :param Iterable[Dict] data: Raw data records
   :param Optional[str] missing_value: Value to use for missing data (default: None)
   :returns: List of cleaned records
   :rtype: List[Dict[str, Any]]

.. autofunction:: clean.save_data

   Save cleaned data into a JSON file.

   :param List[Dict] data: Cleaned data records
   :param str path: Output file path
   :rtype: None

Data Loading
------------

.. automodule:: load_data
   :members:
   :undoc-members:
   :show-inheritance:

**Parsing Functions:**

.. autofunction:: load_data.parse_gpa

   Extract numeric GPA value from string like 'GPA 3.89'.

   :param Optional[str] gpa_str: GPA string to parse
   :returns: Numeric GPA value or None
   :rtype: Optional[float]

   **Examples:**

   .. code-block:: python

      >>> parse_gpa('GPA 3.89')
      3.89
      >>> parse_gpa('3.75')
      3.75
      >>> parse_gpa(None)
      None

.. autofunction:: load_data.parse_gre_score

   Extract numeric GRE score from strings like 'GRE 327', 'GRE V 157'.

   :param Optional[str] gre_str: GRE score string to parse
   :returns: Numeric score or None
   :rtype: Optional[float]

.. autofunction:: load_data.parse_date

   Parse date string like 'January 31, 2026' to date object.

   :param Optional[str] date_str: Date string to parse
   :returns: Date object or None if parsing fails
   :rtype: Optional[datetime.date]

.. autofunction:: load_data.extract_p_id_from_url

   Extract the ID from the GradCafe URL.

   :param Optional[str] url: GradCafe URL
   :returns: Extracted p_id or None
   :rtype: Optional[int]

   **Example:**

   .. code-block:: python

      >>> extract_p_id_from_url('https://www.thegradcafe.com/survey/result/12345')
      12345

.. autofunction:: load_data.clean_string

   Remove NUL characters from string.

   :param Optional[str] s: String to clean
   :returns: Cleaned string or None
   :rtype: Optional[str]

**Database Functions:**

.. autofunction:: load_data.create_applicants_table

   Create the applicants table in the database.

   :param connection conn: PostgreSQL connection object
   :rtype: None

.. autofunction:: load_data.load_json_data

   Load JSON data from file and insert into database.

   Reads JSON lines format, parses each record, and performs batch insertion
   with automatic duplicate handling via ON CONFLICT.

   :param str json_file_path: Path to JSON lines file
   :param connection conn: PostgreSQL connection object
   :returns: Total number of records inserted
   :rtype: int

.. autofunction:: load_data.verify_data

   Display statistics about the loaded data.

   :param connection conn: PostgreSQL connection object
   :rtype: None

.. autofunction:: load_data.main

   Main function to create table and load data.

   Connects to database, creates table if needed, loads data from
   ``llm_extend_applicant_data.json``, and displays verification statistics.

   :rtype: None

Database Queries
----------------

.. automodule:: query_data
   :members:
   :undoc-members:
   :show-inheritance:

**Connection Management:**

.. autofunction:: query_data.get_connection

   Create and return a database connection.

   Uses DATABASE_URL environment variable if set, otherwise uses individual
   DB_* environment variables or defaults.

   :returns: PostgreSQL connection object
   :rtype: psycopg.connection

**Query Functions:**

.. autofunction:: query_data.question_1

   How many entries do you have in your database who have applied for Fall 2026?

   :param connection conn: Database connection
   :returns: Count of Fall 2026 applicants
   :rtype: int

.. autofunction:: query_data.question_2

   What percentage of entries are from international students?

   :param connection conn: Database connection
   :returns: Percentage of international students
   :rtype: float

.. autofunction:: query_data.question_3

   What are the average GPA and GRE scores?

   :param connection conn: Database connection
   :returns: Dictionary with average scores
   :rtype: Dict[str, float]

   **Return Format:**

   .. code-block:: python

      {
          "avg_gpa": 3.75,
          "avg_gre": 325.5,
          "avg_gre_v": 162.3,
          "avg_gre_aw": 4.2
      }

.. autofunction:: query_data.question_4

   What is the average GPA for American students applying for Fall 2026?

   :param connection conn: Database connection
   :returns: Average GPA
   :rtype: float

.. autofunction:: query_data.question_5

   What percentage of applicants for Fall 2026 were accepted?

   :param connection conn: Database connection
   :returns: Acceptance percentage
   :rtype: float

.. autofunction:: query_data.question_6

   What is the average GPA of accepted applicants for Fall 2026?

   :param connection conn: Database connection
   :returns: Average GPA
   :rtype: float

.. autofunction:: query_data.question_7

   How many unique universities are represented?

   :param connection conn: Database connection
   :returns: Count of unique universities
   :rtype: int

.. autofunction:: query_data.question_8

   How many unique programs are represented?

   :param connection conn: Database connection
   :returns: Count of unique programs
   :rtype: int

.. autofunction:: query_data.question_9

   Compare counts using LLM-generated vs original fields.

   :param connection conn: Database connection
   :returns: Tuple of (llm_count, original_count)
   :rtype: Tuple[int, int]

.. autofunction:: query_data.question_10

   Top 10 most applied-to programs for Fall 2026.

   :param connection conn: Database connection
   :returns: List of (university, program, count) tuples
   :rtype: List[Tuple[str, str, int]]

.. autofunction:: query_data.question_11

   Compare PhD vs Masters acceptance rates.

   :param connection conn: Database connection
   :returns: List of degree statistics
   :rtype: List[Tuple]

   **Return Format:**

   .. code-block:: python

      [
          (degree, total_count, accepted_count, acceptance_rate, avg_gpa, gpa_count),
          ...
      ]

.. autofunction:: query_data.main

   Main function to run all queries.

   Connects to database, executes all 11 queries, prints results, and closes connection.

   :rtype: None

Data Types
----------

Common data types used throughout the API:

**Entry Dictionary:**

.. code-block:: python

   Entry = TypedDict('Entry', {
       'url': str,
       'university': str,
       'program_name': str,
       'comments': Optional[str],
       'date_posted': str,
       'applicant_status': str,
       'start_term': str,
       'citizenship': str,
       'gpa': Optional[str],
       'gre_score': Optional[str],
       'gre_v': Optional[str],
       'gre_aw': Optional[str],
       'degree': str,
       'llm_generated_program': Optional[str],
       'llm_generated_university': Optional[str]
   })

**Database Record:**

.. code-block:: python

   Record = Tuple[
       int,    # p_id
       str,    # program
       str,    # comments
       date,   # date_added
       str,    # url
       str,    # status
       str,    # term
       str,    # us_or_international
       float,  # gpa
       float,  # gre
       float,  # gre_v
       float,  # gre_aw
       str,    # degree
       str,    # llm_generated_program
       str     # llm_generated_university
   ]

Error Handling
--------------

All modules implement consistent error handling:

**Common Exceptions:**

* ``FileNotFoundError`` - Data file not found
* ``json.JSONDecodeError`` - Invalid JSON format
* ``psycopg.Error`` - Database connection or query errors
* ``ValueError`` - Invalid data format
* ``RuntimeError`` - System busy (concurrent operations)

**Error Response Format:**

.. code-block:: python

   {
       "status": "error",
       "message": "Description of what went wrong",
       "timestamp": "2026-02-09T15:30:45.123456"
   }
