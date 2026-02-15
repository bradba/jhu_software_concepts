Setup & Installation
====================

This guide covers installation, configuration, and running the application.

Prerequisites
-------------

**System Requirements:**

* Python 3.11 or higher
* PostgreSQL 12 or higher
* 500MB free disk space (for data files)

**Python Dependencies:**

Install all dependencies using pip:

.. code-block:: bash

   pip install -r requirements.txt

Or install manually:

.. code-block:: bash

   pip install psycopg2-binary flask reportlab beautifulsoup4 urllib3 pytest pytest-cov

**Database Setup:**

Ensure PostgreSQL is running and accessible:

.. code-block:: bash

   # Check PostgreSQL status
   pg_isready

   # Default connection: localhost:5432
   # Database: bradleyballinger (or configure via environment variables)

Environment Variables
---------------------

The application uses environment variables for configuration. You have three options:

Option 1: DATABASE_URL (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use a PostgreSQL connection string:

.. code-block:: bash

   export DATABASE_URL="postgresql://username:password@hostname:port/database"

Example:

.. code-block:: bash

   export DATABASE_URL="postgresql://myuser:mypass@localhost:5432/gradcafe_db"

Option 2: Individual Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set each parameter separately:

.. code-block:: bash

   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=gradcafe_db
   export DB_USER=myuser
   export DB_PASSWORD=mypassword

Option 3: Setup Script
~~~~~~~~~~~~~~~~~~~~~~

Create a setup script from the example:

.. code-block:: bash

   cp setup_env_example.sh setup_env.sh
   # Edit setup_env.sh with your credentials
   source setup_env.sh

**Available Environment Variables:**

.. list-table::
   :header-rows: 1
   :widths: 25 50 25

   * - Variable
     - Description
     - Default
   * - ``DATABASE_URL``
     - Full PostgreSQL connection string
     - *(none)*
   * - ``DB_HOST``
     - Database hostname
     - ``localhost``
   * - ``DB_PORT``
     - Database port
     - ``5432``
   * - ``DB_NAME``
     - Database name
     - ``bradleyballinger``
   * - ``DB_USER``
     - Database username
     - ``bradleyballinger``
   * - ``DB_PASSWORD``
     - Database password
     - *(empty)*
   * - ``LLM_API_URL``
     - LLM standardization API endpoint
     - ``http://localhost:8000/standardize``
   * - ``TEST_DATABASE_URL``
     - Test database connection (for integration tests)
     - *(uses main DB config)*

Quick Start
-----------

Using Convenience Scripts (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The project includes shell scripts that handle environment setup automatically:

.. code-block:: bash

   # Step 1: Load data into database
   ./run_load_data.sh

   # Step 2: Run queries (optional, to verify data)
   ./run_queries.sh

   # Step 3: Start the web application
   ./run_app.sh

The web application will be available at: http://127.0.0.1:5001

Manual Setup
~~~~~~~~~~~~

If you prefer to run commands directly:

.. code-block:: bash

   # Step 1: Load data
   python src/load_data.py

   # Step 2: Run queries (optional)
   python src/query_data.py

   # Step 3: Start Flask app
   python src/app.py

Running Tests
-------------

See the :doc:`testing` guide for detailed information on running tests.

Quick test commands:

.. code-block:: bash

   # Run all tests
   ./run_tests.sh

   # Run with coverage
   ./run_tests.sh coverage

   # Run specific categories
   ./run_tests.sh integration
   ./run_tests.sh unit

Docker Setup (Optional)
-----------------------

If you prefer to use Docker:

.. code-block:: bash

   # Start PostgreSQL with Docker
   docker run -d \\
     --name gradcafe-postgres \\
     -e POSTGRES_DB=gradcafe_db \\
     -e POSTGRES_USER=graduser \\
     -e POSTGRES_PASSWORD=gradpass \\
     -p 5432:5432 \\
     postgres:15

   # Set environment variables
   export DATABASE_URL="postgresql://graduser:gradpass@localhost:5432/gradcafe_db"

   # Run the application
   ./run_load_data.sh
   ./run_app.sh

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Database Connection Errors:**

.. code-block:: text

   psycopg2.OperationalError: could not connect to server

**Solution:** Verify PostgreSQL is running and credentials are correct:

.. code-block:: bash

   # Test connection
   psql -h localhost -U your_username -d your_database

**Import Errors:**

.. code-block:: text

   ModuleNotFoundError: No module named 'psycopg2'

**Solution:** Install missing dependencies:

.. code-block:: bash

   pip install -r requirements.txt

**Port Already in Use:**

.. code-block:: text

   OSError: [Errno 48] Address already in use

**Solution:** Change Flask port in ``src/app.py`` or stop conflicting process:

.. code-block:: bash

   # Find process using port 5001
   lsof -i :5001

   # Change port in app.py
   # app.run(debug=True, port=5002)

Next Steps
----------

* Read the :doc:`architecture` guide to understand the system design
* Explore the :doc:`api` reference for module documentation
* See the :doc:`testing` guide for testing conventions
