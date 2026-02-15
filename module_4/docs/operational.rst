Operational Notes
=================

This section provides operational guidelines for running the application in development, production, and CI environments.

Busy-State Policy
-----------------

Overview
~~~~~~~~

The application implements a busy-state mechanism to prevent concurrent operations that could corrupt data or cause race conditions.

**Protected Operations:**

* Data scraping and insertion (``/pull-data`` endpoint)
* LLM-based data enrichment (``/update-analysis`` endpoint)

Implementation
~~~~~~~~~~~~~~

The busy state is managed using a global flag in the Flask application:

.. code-block:: python

   app_state = {
       'is_busy': False,
       'current_operation': None
   }

**State Transitions:**

1. **Idle → Busy**: When an endpoint starts processing
2. **Busy → Idle**: After successful completion or error

**Error Handling:**

If an operation fails, the busy state is automatically cleared in the ``finally`` block to prevent deadlock:

.. code-block:: python

   try:
       app_state['is_busy'] = True
       app_state['current_operation'] = 'pull_data'
       # ... perform operation
   finally:
       app_state['is_busy'] = False
       app_state['current_operation'] = None

Concurrent Request Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a request arrives while the system is busy:

* **HTTP Status**: 409 Conflict
* **Response**: JSON with status, message, and current operation
* **Client Behavior**: Should retry after delay or notify user

Example response:

.. code-block:: json

   {
       "status": "busy",
       "message": "System is currently busy with: pull_data",
       "current_operation": "pull_data",
       "timestamp": "2026-02-14T15:30:45.123456"
   }

Best Practices
~~~~~~~~~~~~~~

**For Development:**

* Use the web interface buttons which handle busy state automatically
* Check ``/`` endpoint response for ``is_busy`` flag before scripting operations

**For Production:**

* Implement exponential backoff for automated processes
* Monitor busy state duration to detect stuck operations
* Set up alerts for operations exceeding expected duration

**For CI/CD:**

* Run operations sequentially in deployment scripts
* Add timeout checks to prevent indefinite waits
* Use health check endpoint to verify system is idle before deployment

Idempotency Strategy
--------------------

Overview
~~~~~~~~

The application is designed to safely handle repeated operations without causing duplicate data or errors.

Database Operations
~~~~~~~~~~~~~~~~~~~

**INSERT Operations:**

All database insertions use ``ON CONFLICT DO NOTHING`` to ensure idempotency:

.. code-block:: sql

   INSERT INTO applicants (p_id, program, comments, ...)
   VALUES (%s, %s, %s, ...)
   ON CONFLICT (p_id) DO NOTHING;

**Benefits:**

* Safe to run data loading multiple times
* Prevents duplicate entries
* Returns count of actual insertions vs. skipped duplicates

**Example Output:**

.. code-block:: json

   {
       "status": "success",
       "inserted": 42,
       "skipped": 158,
       "message": "Successfully added 42 new entries to database"
   }

Scraping Operations
~~~~~~~~~~~~~~~~~~~

The scraper is designed to be idempotent:

1. **Fetches latest data** from GradCafe
2. **Extracts unique IDs** from URLs
3. **Database insertion** automatically handles duplicates via primary key conflict
4. **Reports results** showing new vs. existing entries

**Safe Behaviors:**

* Running scraper multiple times won't create duplicates
* Overlapping scrape ranges are handled gracefully
* Network failures can be retried without data corruption

File Operations
~~~~~~~~~~~~~~~

When saving scraped data to JSON:

* **Overwrites existing files** - last scrape wins
* **Temporary files** used during LLM enrichment
* **Transaction-based loading** - all-or-nothing for each batch

**Recommendations:**

* Archive important scrape results before re-scraping
* Use version control for data files in development
* Implement backup strategy for production data

Retry Strategy
~~~~~~~~~~~~~~

For transient failures:

.. code-block:: python

   # Safe to retry these operations:
   - Database connection failures
   - Network timeouts during scraping
   - LLM API timeouts

   # NOT safe to retry without cleanup:
   - Partial batch insertions (use transactions)
   - File write failures (may leave corrupt files)

Uniqueness Keys
---------------

Primary Keys
~~~~~~~~~~~~

**applicants table:**

.. code-block:: sql

   p_id INTEGER PRIMARY KEY

The ``p_id`` is extracted from the GradCafe URL and serves as the natural primary key.

**Properties:**

* Globally unique across GradCafe
* Immutable (never changes for a given entry)
* Sequential but not necessarily contiguous
* Used for deduplication during data loading

Extraction
~~~~~~~~~~

The ``p_id`` is extracted from URLs using regex:

.. code-block:: python

   def extract_p_id_from_url(url):
       """Extract the ID from the GradCafe URL."""
       # Example: https://www.thegradcafe.com/survey/result/12345
       match = re.search(r'/result/(\d+)', url)
       return int(match.group(1)) if match else None

**Validation:**

* Records without extractable ``p_id`` are skipped
* Logged with warning message including line number
* Counted in ``skipped`` metric

Composite Uniqueness
~~~~~~~~~~~~~~~~~~~~~

While ``p_id`` is the primary key, data quality can be assessed using additional fields:

**Quasi-unique combinations:**

* ``(university, program, start_term, applicant_status, date_posted)``
* ``(p_id, date_posted)`` - should always be 1:1

**Use in queries:**

.. code-block:: sql

   -- Count unique programs
   SELECT COUNT(DISTINCT program) FROM applicants;

   -- Count unique universities
   SELECT COUNT(DISTINCT university) FROM applicants;

   -- Find potential duplicates (should return 0)
   SELECT p_id, COUNT(*)
   FROM applicants
   GROUP BY p_id
   HAVING COUNT(*) > 1;

Index Strategy
~~~~~~~~~~~~~~

For optimal query performance:

.. code-block:: sql

   -- Primary key index (automatic)
   CREATE INDEX ON applicants(p_id);

   -- Common query patterns (recommended for production)
   CREATE INDEX ON applicants(start_term);
   CREATE INDEX ON applicants(applicant_status);
   CREATE INDEX ON applicants(us_or_international);
   CREATE INDEX ON applicants(degree);

Data Integrity Checks
~~~~~~~~~~~~~~~~~~~~~

Verify uniqueness after loading:

.. code-block:: python

   # Check for duplicate p_ids
   cursor.execute("""
       SELECT COUNT(*), COUNT(DISTINCT p_id)
       FROM applicants
   """)
   total, unique = cursor.fetchone()
   assert total == unique, "Duplicate p_ids detected!"

Troubleshooting
---------------

Common Local Issues
~~~~~~~~~~~~~~~~~~~

**Issue: Database connection refused**

.. code-block:: text

   psycopg.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed

**Solutions:**

1. Check if PostgreSQL is running:

   .. code-block:: bash

      # macOS (Homebrew)
      brew services list
      brew services start postgresql@14

      # Linux (systemd)
      sudo systemctl status postgresql
      sudo systemctl start postgresql

      # Check port
      lsof -i :5432

2. Verify connection parameters:

   .. code-block:: bash

      # Test connection
      psql -h localhost -p 5432 -U bradleyballinger

      # Set environment variables
      export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

3. Check PostgreSQL logs:

   .. code-block:: bash

      # macOS (Homebrew)
      tail -f /usr/local/var/log/postgresql@14.log

      # Linux
      sudo tail -f /var/log/postgresql/postgresql-14-main.log

**Issue: Permission denied on database**

.. code-block:: text

   psycopg.ProgrammingError: permission denied for table applicants

**Solutions:**

1. Grant necessary permissions:

   .. code-block:: sql

      GRANT ALL PRIVILEGES ON DATABASE your_db TO your_user;
      GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;

2. Or use a superuser account for development:

   .. code-block:: bash

      export DB_USER=postgres

**Issue: Module import errors**

.. code-block:: text

   ModuleNotFoundError: No module named 'psycopg'

**Solutions:**

1. Install dependencies:

   .. code-block:: bash

      pip install -r requirements.txt

2. Verify Python environment:

   .. code-block:: bash

      which python
      pip list | grep psycopg

3. Ensure correct virtual environment is activated:

   .. code-block:: bash

      source venv/bin/activate

**Issue: Tests failing with coverage errors**

.. code-block:: text

   Coverage failure: total of 94 is less than fail-under=100

**Solutions:**

1. Run tests without coverage to see actual failures:

   .. code-block:: bash

      pytest tests/ -v --no-cov

2. Check for new code paths not covered by tests

3. Review ``htmlcov/index.html`` for line-by-line coverage:

   .. code-block:: bash

      pytest --cov=src --cov-report=html
      open htmlcov/index.html

**Issue: Flask app not starting**

.. code-block:: text

   Address already in use

**Solutions:**

1. Find and kill process using port 5001:

   .. code-block:: bash

      # Find process
      lsof -i :5001

      # Kill process
      kill -9 <PID>

2. Use different port:

   .. code-block:: bash

      FLASK_PORT=5002 python src/app.py

Common CI/CD Issues
~~~~~~~~~~~~~~~~~~~

**Issue: Tests pass locally but fail in CI**

**Possible causes:**

1. **Different PostgreSQL versions**

   .. code-block:: yaml

      # GitHub Actions example
      services:
        postgres:
          image: postgres:14
          env:
            POSTGRES_PASSWORD: postgres
          options: >-
            --health-cmd pg_isready
            --health-interval 10s
            --health-timeout 5s
            --health-retries 5

2. **Environment variables not set**

   .. code-block:: yaml

      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        DB_NAME: test_db

3. **Missing dependencies in CI environment**

   .. code-block:: yaml

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install psycopg[binary]

**Issue: Database tests timeout in CI**

**Solutions:**

1. Increase test timeout:

   .. code-block:: ini

      # pytest.ini
      [pytest]
      timeout = 300

2. Use faster test database:

   .. code-block:: bash

      # Use in-memory or tmpfs for test DB
      export TEST_DATABASE_URL="postgresql://localhost/test?options=-c%20fsync=off"

3. Run database tests in parallel with caution:

   .. code-block:: bash

      pytest tests/ -n 4 --dist loadscope

**Issue: Intermittent test failures**

**Common causes:**

1. **Race conditions in busy-state tests**

   .. code-block:: python

      # Add small delays in tests
      time.sleep(0.1)

2. **Database state not cleaned between tests**

   .. code-block:: python

      @pytest.fixture(autouse=True)
      def cleanup_database(test_db_connection):
          yield
          # Cleanup after each test
          cursor = test_db_connection.cursor()
          cursor.execute("TRUNCATE TABLE test_applicants CASCADE")
          test_db_connection.commit()

3. **Non-deterministic test order**

   .. code-block:: bash

      # Run tests in random order to detect issues
      pytest --random-order

Performance Issues
~~~~~~~~~~~~~~~~~~

**Issue: Slow data loading**

**Optimization strategies:**

1. **Batch size tuning:**

   .. code-block:: python

      # Adjust batch size in load_data.py
      if len(records) >= 5000:  # Larger batches
          cursor.executemany(insert_query, records)

2. **Disable autocommit during bulk loading:**

   .. code-block:: python

      conn.autocommit = False
      # ... perform bulk operations
      conn.commit()

3. **Use COPY for large datasets:**

   .. code-block:: python

      # For millions of records
      cursor.copy_from(file, 'applicants', sep=',')

**Issue: Slow queries**

**Diagnostic steps:**

1. **Enable query logging:**

   .. code-block:: python

      import logging
      logging.basicConfig(level=logging.DEBUG)

2. **Use EXPLAIN ANALYZE:**

   .. code-block:: sql

      EXPLAIN ANALYZE
      SELECT COUNT(*) FROM applicants WHERE start_term = 'Fall 2026';

3. **Add indexes for common queries:**

   .. code-block:: sql

      CREATE INDEX idx_start_term ON applicants(start_term);
      CREATE INDEX idx_status ON applicants(applicant_status);

Memory Issues
~~~~~~~~~~~~~

**Issue: Out of memory during data loading**

**Solutions:**

1. **Use streaming instead of loading entire file:**

   .. code-block:: python

      # Already implemented in load_data.py
      with open(json_file_path, 'r') as f:
          for line in f:  # Processes one line at a time
              data = json.loads(line)

2. **Reduce batch size:**

   .. code-block:: python

      # Commit more frequently
      if len(records) >= 500:  # Smaller batches
          cursor.executemany(insert_query, records)

3. **Monitor memory usage:**

   .. code-block:: bash

      # During execution
      watch -n 1 'ps aux | grep python | grep -v grep'

Health Checks
-------------

Application Health
~~~~~~~~~~~~~~~~~~

**Endpoint:** ``GET /``

**Response includes:**

.. code-block:: javascript

   {
       "is_busy": false,
       "current_operation": null,
       "query_results": { /* ... query data ... */ }
   }

**Health check script:**

.. code-block:: bash

   #!/bin/bash
   # check_health.sh

   RESPONSE=$(curl -s http://localhost:5001/)
   IS_BUSY=$(echo $RESPONSE | jq -r '.is_busy // true')

   if [ "$IS_BUSY" = "false" ]; then
       echo "Application healthy and idle"
       exit 0
   else
       echo "Application busy or unhealthy"
       exit 1
   fi

Database Health
~~~~~~~~~~~~~~~

**Check connection:**

.. code-block:: bash

   #!/bin/bash
   # check_db.sh

   psql $DATABASE_URL -c "SELECT 1" > /dev/null 2>&1
   if [ $? -eq 0 ]; then
       echo "Database healthy"
       exit 0
   else
       echo "Database connection failed"
       exit 1
   fi

**Check data integrity:**

.. code-block:: python

   def check_database_health(conn):
       """Verify database health and data integrity."""
       cursor = conn.cursor()

       # Check table exists
       cursor.execute("""
           SELECT COUNT(*) FROM information_schema.tables
           WHERE table_name = 'applicants'
       """)
       if cursor.fetchone()[0] == 0:
           return False, "Table 'applicants' not found"

       # Check for data
       cursor.execute("SELECT COUNT(*) FROM applicants")
       count = cursor.fetchone()[0]
       if count == 0:
           return False, "No data in applicants table"

       # Check for duplicates
       cursor.execute("""
           SELECT COUNT(*) FROM (
               SELECT p_id FROM applicants
               GROUP BY p_id HAVING COUNT(*) > 1
           ) AS duplicates
       """)
       duplicates = cursor.fetchone()[0]
       if duplicates > 0:
           return False, f"Found {duplicates} duplicate p_ids"

       return True, f"Healthy: {count} records, no duplicates"

Monitoring
----------

Key Metrics
~~~~~~~~~~~

**Application metrics:**

* Request rate (requests/minute)
* Busy state duration (seconds)
* Error rate (errors/requests)
* Response time (milliseconds)

**Database metrics:**

* Connection pool usage
* Query execution time
* Insert rate (records/second)
* Duplicate rate (duplicates/inserts)

**Scraper metrics:**

* Scrape duration (seconds)
* Records fetched per scrape
* Network error rate
* LLM API call duration

Logging
~~~~~~~

**Application logs:**

.. code-block:: python

   import logging

   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('app.log'),
           logging.StreamHandler()
       ]
   )

**Key events to log:**

* Application startup/shutdown
* Database connections/disconnections
* Scraping operations start/complete
* Busy state changes
* Errors and exceptions
* Performance warnings (slow queries, etc.)

Alerting
~~~~~~~~

**Recommended alerts:**

1. **Busy state stuck** - operation running > 10 minutes
2. **High error rate** - > 5% of requests failing
3. **Database connection failures** - any connection errors
4. **Low disk space** - < 10% free space
5. **High memory usage** - > 80% memory used

Best Practices
--------------

Development
~~~~~~~~~~~

* Use local PostgreSQL for development
* Keep test data small (<1000 records)
* Run tests before committing code
* Use environment variables for all configuration
* Never commit ``.env`` or ``setup_env.sh`` files

Staging
~~~~~~~

* Use separate database from production
* Test with production-like data volume
* Monitor performance metrics
* Validate all queries return expected results
* Test failure scenarios (network errors, DB failures)

Production
~~~~~~~~~~

* Use connection pooling for database
* Implement rate limiting for scraper
* Set up monitoring and alerting
* Regular database backups
* Document runbooks for common issues
* Use read replicas for analytics queries

Backup and Recovery
-------------------

Database Backups
~~~~~~~~~~~~~~~~

**Full backup:**

.. code-block:: bash

   # Backup database
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

   # Restore database
   psql $DATABASE_URL < backup_20260214_150000.sql

**Incremental backups:**

.. code-block:: bash

   # Enable WAL archiving in postgresql.conf
   archive_mode = on
   archive_command = 'cp %p /path/to/archive/%f'

**Automated backups:**

.. code-block:: bash

   #!/bin/bash
   # backup.sh - Run daily via cron

   BACKUP_DIR="/backups/postgresql"
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   FILENAME="applicants_${TIMESTAMP}.sql"

   pg_dump -t applicants $DATABASE_URL | gzip > "${BACKUP_DIR}/${FILENAME}.gz"

   # Keep only last 30 days
   find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

Disaster Recovery
~~~~~~~~~~~~~~~~~

**Recovery procedures:**

1. **Restore from most recent backup**
2. **Verify data integrity** using health checks
3. **Re-run scraper** to fetch latest data
4. **Validate query results** against known values
5. **Resume normal operations**

**Testing recovery:**

* Practice recovery quarterly
* Document actual recovery time
* Update runbooks based on experience
* Test with both full and incremental backups
