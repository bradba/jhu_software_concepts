Testing Guide
=============

This guide explains how to run tests, use test markers, and understand the test fixtures and doubles provided in the test suite.

Test Suite Overview
-------------------

The project includes a comprehensive test suite with **166 tests** achieving **100% code coverage**.

**Test Statistics:**

* Total tests: 166
* Code coverage: 100%
* Test files: 10
* Test categories: Unit tests, integration tests, database tests, endpoint tests

Running Tests
-------------

Using Test Script (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``run_tests.sh`` script provides convenient options for running tests:

.. code-block:: bash

   # Run all tests with coverage report
   ./run_tests.sh

   # Run with detailed coverage report
   ./run_tests.sh coverage

   # Run specific test categories
   ./run_tests.sh integration  # Integration tests only
   ./run_tests.sh unit        # Unit tests only
   ./run_tests.sh db          # Database tests only
   ./run_tests.sh buttons     # Flask endpoint tests only

   # Other options
   ./run_tests.sh verbose     # Verbose output (-v)
   ./run_tests.sh quick       # Quick run without coverage
   ./run_tests.sh help        # Show all options

Using pytest Directly
~~~~~~~~~~~~~~~~~~~~~

Run tests directly with pytest for more control:

.. code-block:: bash

   # Run all tests
   pytest tests/

   # Run with coverage report
   pytest tests/ --cov=src --cov-report=term-missing

   # Run specific test file
   pytest tests/test_query_data_unit.py -v

   # Run tests matching a pattern
   pytest tests/ -k "test_parse_gpa"

   # Run with verbose output
   pytest tests/ -v

Test Markers
------------

The test suite uses pytest markers to categorize tests. You can run specific categories using the ``-m`` flag.

Available Markers
~~~~~~~~~~~~~~~~~

**@pytest.mark.db**
  Tests that require a real PostgreSQL database connection.

  .. code-block:: bash

     # Run only database tests
     pytest tests/ -m db

  Example test:

  .. code-block:: python

     @pytest.mark.db
     def test_create_table(test_db_connection):
         """Test table creation in PostgreSQL."""
         load_data.create_applicants_table(test_db_connection)
         # ... verify table exists

**@pytest.mark.integration**
  End-to-end integration tests that test multiple components together.

  .. code-block:: bash

     # Run only integration tests
     pytest tests/ -m integration

  Example test:

  .. code-block:: python

     @pytest.mark.integration
     def test_end_to_end_data_pipeline(test_db_connection):
         """Test complete ETL pipeline from JSON to database."""
         # ... test scrape -> clean -> load -> query

**@pytest.mark.buttons**
  Tests for Flask web application endpoints and button functionality.

  .. code-block:: bash

     # Run only Flask endpoint tests
     pytest tests/ -m buttons

  Example test:

  .. code-block:: python

     @pytest.mark.buttons
     def test_pull_data_endpoint(client, monkeypatch):
         """Test /pull-data endpoint."""
         # ... mock scraper and test endpoint

Combining Markers
~~~~~~~~~~~~~~~~~

You can combine markers using boolean expressions:

.. code-block:: bash

   # Run database tests but exclude integration tests
   pytest tests/ -m "db and not integration"

   # Run either unit or integration tests
   pytest tests/ -m "unit or integration"

Test Fixtures
-------------

The test suite provides several fixtures for common testing needs.

Database Fixtures
~~~~~~~~~~~~~~~~~

**test_db_connection**
  Provides a PostgreSQL database connection for testing.

  * Scope: function (new connection per test)
  * Cleanup: Automatically closes connection after test
  * Configuration: Uses TEST_DATABASE_URL or DB_* environment variables

  Usage:

  .. code-block:: python

     @pytest.mark.db
     def test_database_operation(test_db_connection):
         cursor = test_db_connection.cursor()
         cursor.execute("SELECT COUNT(*) FROM applicants")
         count = cursor.fetchone()[0]
         assert count >= 0

**test_db_table**
  Provides a database connection with an empty applicants table.

  * Scope: function
  * Setup: Creates applicants table, clears existing data
  * Cleanup: Closes connection after test

  Usage:

  .. code-block:: python

     @pytest.mark.db
     def test_insert_data(test_db_table):
         # Table is empty and ready for inserts
         load_data.load_json_data("test_data.json", test_db_table)
         # ... verify insertions

Flask Application Fixtures
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**test_app**
  Provides a configured Flask application instance for testing.

  * Scope: function
  * Configuration: Sets TESTING=True

  Usage:

  .. code-block:: python

     def test_app_configuration(test_app):
         assert test_app.config['TESTING'] is True
         assert test_app.debug is False

**client**
  Provides a Flask test client for making HTTP requests.

  * Scope: function
  * Dependencies: Uses test_app fixture

  Usage:

  .. code-block:: python

     def test_index_page(client):
         response = client.get('/')
         assert response.status_code == 200
         assert b'Graduate School Applicant Database' in response.data

Test Data Fixtures
~~~~~~~~~~~~~~~~~~

**fake_scraper_data**
  Provides sample scraped data for testing.

  * Returns: List of dictionaries with applicant data
  * Use case: Testing data cleaning and loading without real scraping

  Usage:

  .. code-block:: python

     def test_clean_data(fake_scraper_data):
         cleaned = clean.clean_data(fake_scraper_data)
         assert len(cleaned) == len(fake_scraper_data)
         assert cleaned[0]['university'] == 'Stanford University'

**sample_json_data**
  Provides sample JSON data matching the database schema.

  Usage:

  .. code-block:: python

     def test_json_parsing(sample_json_data, tmp_path):
         # Write sample data to temporary file
         json_file = tmp_path / "test_data.json"
         with open(json_file, 'w') as f:
             for record in sample_json_data:
                 f.write(json.dumps(record) + '\n')
         # ... test loading

Test Doubles and Mocking
-------------------------

The test suite uses several patterns for test doubles and mocking to isolate units under test.

Monkeypatch for Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests use ``monkeypatch`` to set environment variables without affecting other tests:

.. code-block:: python

   def test_database_url_parsing(monkeypatch):
       """Test DATABASE_URL environment variable parsing."""
       monkeypatch.setenv('DATABASE_URL',
                          'postgresql://user:pass@host:5433/testdb')

       conn = query_data.get_connection()
       # ... verify connection parameters

Mock External Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Mocking subprocess calls:**

.. code-block:: python

   def test_scraper_subprocess(monkeypatch):
       """Mock subprocess call to scraper."""
       def mock_run(*args, **kwargs):
           return type('obj', (object,), {'returncode': 0})()

       monkeypatch.setattr('subprocess.run', mock_run)
       # ... test code that calls subprocess

**Mocking HTTP requests:**

.. code-block:: python

   def test_llm_api_call(monkeypatch):
       """Mock HTTP request to LLM API."""
       def mock_get(*args, **kwargs):
           return type('Response', (), {
               'json': lambda: {'university': 'Stanford University'},
               'status_code': 200
           })()

       monkeypatch.setattr('requests.get', mock_get)
       # ... test LLM integration

**Mocking file operations:**

.. code-block:: python

   def test_file_loading(tmp_path):
       """Use tmp_path for file operations."""
       test_file = tmp_path / "test_data.json"
       test_file.write_text('{"test": "data"}')

       data = clean.load_data(str(test_file))
       assert data == {"test": "data"}

Patching Database Connections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For unit tests that don't need a real database:

.. code-block:: python

   def test_query_without_db(monkeypatch):
       """Test query logic without database."""
       mock_cursor = Mock()
       mock_cursor.fetchone.return_value = (42,)

       mock_conn = Mock()
       mock_conn.cursor.return_value = mock_cursor

       result = query_data.question_1(mock_conn)
       assert result == 42

Test Organization
-----------------

Test File Structure
~~~~~~~~~~~~~~~~~~~

Tests are organized by module and test type:

.. code-block:: text

   tests/
   ├── test_analysis_format.py      # Output format validation
   ├── test_app_errors.py           # Flask error handling
   ├── test_buttons.py              # Flask endpoint functionality
   ├── test_clean_unit.py           # Data cleaning unit tests
   ├── test_db_insert.py            # Database insertion tests
   ├── test_flask_page.py           # Flask page rendering
   ├── test_integration_end_to_end.py  # End-to-end tests
   ├── test_load_data_unit.py       # Data loading unit tests
   ├── test_query_data_unit.py      # Query function unit tests
   └── test_scrape_unit.py          # Web scraping unit tests

Test Naming Conventions
~~~~~~~~~~~~~~~~~~~~~~~

Tests follow a consistent naming pattern:

* **test_<module>_unit.py**: Unit tests for a specific module
* **test_<feature>_integration.py**: Integration tests for a feature
* **test_<component>.py**: Component-specific tests (buttons, flask_page)

Individual test functions use descriptive names:

.. code-block:: python

   def test_parse_gpa_with_valid_input():
       """Test GPA parsing with valid 'GPA 3.89' format."""

   def test_parse_gpa_with_missing_value():
       """Test GPA parsing handles None input."""

   def test_parse_gpa_with_invalid_format():
       """Test GPA parsing returns None for invalid format."""

Running Specific Test Categories
---------------------------------

By Module
~~~~~~~~~

.. code-block:: bash

   # Test data cleaning
   pytest tests/test_clean_unit.py

   # Test database queries
   pytest tests/test_query_data_unit.py

   # Test Flask application
   pytest tests/test_flask_page.py tests/test_buttons.py

By Functionality
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test parsing functions
   pytest tests/ -k "parse"

   # Test error handling
   pytest tests/test_app_errors.py

   # Test database operations
   pytest tests/ -m db

Test Configuration
------------------

Database Configuration for Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration tests use environment variables for database configuration:

.. code-block:: bash

   # Use separate test database
   export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/test_db"
   pytest tests/ -m integration

   # Or use individual DB_* variables
   export DB_NAME=test_database
   export DB_USER=testuser
   pytest tests/ -m db

If not specified, tests use the same defaults as the main application.

Coverage Configuration
~~~~~~~~~~~~~~~~~~~~~~

Coverage settings are configured in ``pyproject.toml`` or ``.coveragerc``:

.. code-block:: bash

   # Run with coverage report
   pytest --cov=src --cov-report=html

   # Open HTML coverage report
   open htmlcov/index.html

Expected Test Output
--------------------

Successful Test Run
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   $ ./run_tests.sh
   ======================== test session starts =========================
   collected 166 items

   tests/test_analysis_format.py .....................      [ 12%]
   tests/test_app_errors.py .................               [ 23%]
   tests/test_buttons.py ............                       [ 30%]
   tests/test_clean_unit.py .......................         [ 44%]
   tests/test_db_insert.py ........                         [ 49%]
   tests/test_flask_page.py .......                         [ 53%]
   tests/test_integration_end_to_end.py ............        [ 60%]
   tests/test_load_data_unit.py ......................      [ 73%]
   tests/test_query_data_unit.py .......................    [ 87%]
   tests/test_scrape_unit.py .....................          [100%]

   ---------- coverage: platform darwin, python 3.11.7 ----------
   Name                      Stmts   Miss  Cover   Missing
   -------------------------------------------------------
   src/__init__.py              0      0   100%
   src/app.py                 145      0   100%
   src/clean.py                86      0   100%
   src/load_data.py           156      0   100%
   src/query_data.py          178      0   100%
   src/scrape.py              112      0   100%
   -------------------------------------------------------
   TOTAL                      677      0   100%

   ======================== 166 passed in 12.34s ========================

Failed Test Example
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   FAILED tests/test_query_data_unit.py::test_question_1 - AssertionError

   ============================= FAILURES =============================
   _________________ test_question_1 __________________

   test_db_connection = <connection object at 0x...>

       def test_question_1(test_db_connection):
           result = query_data.question_1(test_db_connection)
   >       assert result > 0
   E       AssertionError: assert 0 > 0

   tests/test_query_data_unit.py:42: AssertionError

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Database connection errors:**

.. code-block:: text

   psycopg.OperationalError: could not connect to server

Solution: Ensure PostgreSQL is running and environment variables are set correctly:

.. code-block:: bash

   # Check PostgreSQL status
   pg_ctl status

   # Set test database URL
   export TEST_DATABASE_URL="postgresql://localhost:5432/testdb"

**Import errors:**

.. code-block:: text

   ModuleNotFoundError: No module named 'src'

Solution: Ensure you're running pytest from the project root directory.

**Coverage not 100%:**

.. code-block:: text

   TOTAL                      677     15    98%

Solution: Run tests with ``-v`` to identify uncovered lines:

.. code-block:: bash

   pytest --cov=src --cov-report=term-missing -v

Best Practices
--------------

Writing New Tests
~~~~~~~~~~~~~~~~~

1. **Use descriptive names**: Test names should clearly describe what they test
2. **One assertion per concept**: Test one thing at a time
3. **Use fixtures**: Leverage existing fixtures for setup
4. **Add markers**: Tag tests appropriately (``@pytest.mark.db``, etc.)
5. **Mock external dependencies**: Don't make real HTTP calls or subprocess calls in unit tests
6. **Clean up resources**: Use fixtures with teardown or context managers

Example test structure:

.. code-block:: python

   @pytest.mark.db
   def test_insert_applicant_record(test_db_table):
       """Test inserting a single applicant record.

       Verifies that:
       1. Record is inserted successfully
       2. All fields are stored correctly
       3. Duplicate inserts are handled
       """
       # Arrange
       sample_data = [{
           "p_id": 12345,
           "program": "Computer Science",
           # ... other fields
       }]

       # Act
       inserted = load_data.load_json_data("sample.json", test_db_table)

       # Assert
       assert inserted == 1
       cursor = test_db_table.cursor()
       cursor.execute("SELECT COUNT(*) FROM applicants WHERE p_id = 12345")
       assert cursor.fetchone()[0] == 1

Continuous Integration
~~~~~~~~~~~~~~~~~~~~~~

For CI/CD pipelines, use environment variables and the test script:

.. code-block:: yaml

   # GitHub Actions example
   - name: Run tests
     env:
       DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
     run: |
       ./run_tests.sh coverage

Additional Resources
--------------------

* `pytest documentation <https://docs.pytest.org/>`_
* `pytest fixtures <https://docs.pytest.org/en/stable/fixture.html>`_
* `pytest markers <https://docs.pytest.org/en/stable/mark.html>`_
* `unittest.mock <https://docs.python.org/3/library/unittest.mock.html>`_
