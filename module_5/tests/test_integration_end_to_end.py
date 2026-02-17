"""
Integration Tests - End-to-End Workflow
Tests the complete workflow with a real PostgreSQL database.
Uses a test table to avoid interfering with production data.
"""

import json
import os
import re
import sys
from urllib.parse import urlparse

import psycopg
import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class MockSubprocessResult:
    """Mock object for subprocess.run() results."""
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _TestTableCursorWrapper:
    """Wrapper that transparently redirects 'applicants' table to 'test_applicants'."""
    def __init__(self, real_cursor):
        self._cursor = real_cursor

    def execute(self, query, params=None):
        """Execute query with table name replacement."""
        # Replace 'applicants' with 'test_applicants' in the query
        # Use regex to avoid replacing if it's already test_applicants
        if isinstance(query, str):
            # Match 'applicants' but not 'test_applicants'
            # Use negative lookbehind to ensure 'applicants' is not preceded by 'test_'
            modified_query = re.sub(r'(?<!test_)applicants\b', 'test_applicants', query)
        else:
            modified_query = query

        return self._cursor.execute(modified_query, params)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def close(self):
        return self._cursor.close()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __getattr__(self, name):
        """Delegate all other attributes to the real cursor."""
        return getattr(self._cursor, name)


class _TestTableConnectionWrapper:
    """Wrapper that returns _TestTableCursorWrapper for all cursor() calls."""
    def __init__(self, real_connection):
        self._conn = real_connection
        self._closed = False

    def cursor(self):
        """Return a wrapped cursor that uses test table."""
        real_cursor = self._conn.cursor()
        return _TestTableCursorWrapper(real_cursor)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        """Don't actually close the connection - let fixture handle cleanup."""
        self._closed = True
        # Don't close the real connection - the test fixture will handle it

    @property
    def closed(self):
        return self._closed

    def __getattr__(self, name):
        """Delegate all other attributes to the real connection."""
        return getattr(self._conn, name)


@pytest.fixture(scope='module')
def test_db_connection():
    """
    Create a connection to the test database.
    Uses the same database but with a test-specific table.
    Respects DATABASE_URL and DB_* environment variables for test database configuration.
    """
    database_url = os.environ.get('TEST_DATABASE_URL') or os.environ.get('DATABASE_URL')

    if database_url:
        # Parse DATABASE_URL
        parsed = urlparse(database_url)
        conn_params = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'dbname': parsed.path.lstrip('/') if parsed.path else 'bradleyballinger',
            'user': parsed.username or 'bradleyballinger',
        }
        if parsed.password:
            conn_params['password'] = parsed.password
    else:
        # Use individual environment variables or defaults
        conn_params = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': int(os.environ.get('DB_PORT', '5432')),
            'dbname': os.environ.get('DB_NAME', 'bradleyballinger'),
            'user': os.environ.get('DB_USER', 'bradleyballinger'),
        }
        if os.environ.get('DB_PASSWORD'):
            conn_params['password'] = os.environ.get('DB_PASSWORD')

    conn = psycopg.connect(**conn_params)
    conn.autocommit = False

    yield conn

    conn.close()


@pytest.fixture(scope='function')
def test_db_table(test_db_connection):
    """
    Create a test-specific applicants table before each test.
    Clean up after the test completes.
    """
    conn = test_db_connection
    cursor = conn.cursor()

    # Drop table if it exists
    cursor.execute("DROP TABLE IF EXISTS test_applicants CASCADE;")

    # Create test table with same schema as production
    create_table_sql = """
    CREATE TABLE test_applicants (
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
    """
    cursor.execute(create_table_sql)
    conn.commit()
    cursor.close()

    yield conn

    # Clean up after test
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS test_applicants CASCADE;")
    conn.commit()
    cursor.close()


@pytest.fixture
def test_app(monkeypatch, test_db_table):
    """
    Create Flask app configured to use test database table.
    """
    def patched_get_connection():
        """Return wrapped connection that transparently uses test_applicants."""
        return _TestTableConnectionWrapper(test_db_table)

    # Patch query_data.get_connection to return our wrapped connection
    monkeypatch.setattr('query_data.get_connection', patched_get_connection)

    # Import app after patching
    from app import app as flask_app

    flask_app.config['TESTING'] = True
    flask_app.config['DEBUG'] = False

    return flask_app


@pytest.fixture
def client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()


@pytest.fixture
def fake_scraper_data():
    """Fake scraper that returns multiple realistic records."""
    return [
        {
            'url': 'https://www.thegradcafe.com/survey/result/100101',
            'university': 'Stanford University',
            'program_name': 'Computer Science PhD',
            'comments': 'Great funding package',
            'date_posted': 'February 01, 2026',
            'applicant_status': 'Accepted',
            'start_term': 'Fall 2026',
            'citizenship': 'International',
            'gpa': '3.9',
            'gre_score': '330',
            'gre_v': '168',
            'gre_aw': '5.0',
            'degree': 'PhD'
        },
        {
            'url': 'https://www.thegradcafe.com/survey/result/100102',
            'university': 'MIT',
            'program_name': 'Computer Science PhD',
            'comments': 'Interview went well',
            'date_posted': 'February 05, 2026',
            'applicant_status': 'Accepted',
            'start_term': 'Fall 2026',
            'citizenship': 'American',
            'gpa': '3.8',
            'gre_score': '325',
            'gre_v': '165',
            'gre_aw': '4.5',
            'degree': 'PhD'
        },
        {
            'url': 'https://www.thegradcafe.com/survey/result/100103',
            'university': 'UC Berkeley',
            'program_name': 'Data Science MS',
            'comments': 'Quick response',
            'date_posted': 'February 10, 2026',
            'applicant_status': 'Rejected',
            'start_term': 'Fall 2026',
            'citizenship': 'International',
            'gpa': '3.7',
            'gre_score': '320',
            'gre_v': '162',
            'gre_aw': '4.0',
            'degree': 'Masters'
        }
    ]


def setup_pull_data_mocks(monkeypatch, fake_scraper_data):
    """Set up common mocks for pull-data endpoint tests."""
    # Mock subprocess.run for scraper
    def mock_subprocess_run(*_args, **_kwargs):
        return MockSubprocessResult(returncode=0, stdout='Scraping complete')

    monkeypatch.setattr('subprocess.run', mock_subprocess_run)
    monkeypatch.setattr('os.path.exists', lambda path: 'new_applicant_data.json' in str(path))

    # Mock file reading to return fake scraper data
    original_open = open
    def mock_open(path, *args, **kwargs):
        if 'new_applicant_data.json' in str(path):
            class MockFile:
                def __enter__(self):
                    return self
                def __exit__(self, *_args):
                    pass
                def read(self):
                    return json.dumps(fake_scraper_data)
            return MockFile()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr('builtins.open', mock_open)
    monkeypatch.setattr('os.remove', lambda _path: None)


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflow with real database."""

    def test_complete_workflow(self, client, monkeypatch, fake_scraper_data, test_db_table):
        """Test full workflow: pull data, update analysis, render page with real DB."""

        # Set up mocks for scraper
        setup_pull_data_mocks(monkeypatch, fake_scraper_data)

        # Step 1: POST /pull-data - should succeed and insert rows
        pull_response = client.post('/pull-data')
        assert pull_response.status_code == 200, "Pull data should succeed"

        pull_data = json.loads(pull_response.data)
        assert pull_data['status'] == 'success'
        assert pull_data['inserted'] == 3, "Should insert 3 records"
        assert pull_data['skipped'] == 0

        # Step 2: Verify rows are actually in the database
        cursor = test_db_table.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_applicants;")
        count = cursor.fetchone()[0]
        assert count == 3, "Database should contain 3 records"

        # Verify specific p_ids
        cursor.execute("SELECT p_id FROM test_applicants ORDER BY p_id;")
        p_ids = [row[0] for row in cursor.fetchall()]
        assert 100101 in p_ids
        assert 100102 in p_ids
        assert 100103 in p_ids
        cursor.close()

        # Step 3: POST /update-analysis - should succeed
        update_response = client.post('/update-analysis')
        assert update_response.status_code == 200, "Update analysis should succeed"

        update_data = json.loads(update_response.data)
        assert update_data['status'] == 'success'

        # Step 4: GET / (analysis page) - should render successfully
        # The connection wrapper automatically redirects queries to test_applicants
        analysis_response = client.get('/')
        assert analysis_response.status_code == 200

        html_content = analysis_response.data.decode('utf-8')
        # Verify the page contains expected structure
        assert 'Question' in html_content or 'Answer' in html_content

    def test_pull_data_inserts_all_records(self, client, monkeypatch, fake_scraper_data, test_db_table):
        """Test that pull data successfully inserts all records into real database."""

        setup_pull_data_mocks(monkeypatch, fake_scraper_data)

        # Pull data
        response = client.post('/pull-data')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['inserted'] == len(fake_scraper_data)

        # Verify in database
        cursor = test_db_table.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_applicants;")
        count = cursor.fetchone()[0]
        assert count == len(fake_scraper_data)
        cursor.close()

    def test_update_analysis_succeeds_after_pull(self, client, monkeypatch, fake_scraper_data, test_db_table):
        """Test that update analysis succeeds after pulling data."""

        setup_pull_data_mocks(monkeypatch, fake_scraper_data)

        # First, pull data
        pull_response = client.post('/pull-data')
        assert pull_response.status_code == 200

        # Verify data is in database
        cursor = test_db_table.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_applicants;")
        count = cursor.fetchone()[0]
        assert count == 3
        cursor.close()

        # Then, update analysis
        update_response = client.post('/update-analysis')
        assert update_response.status_code == 200

        update_data = json.loads(update_response.data)
        assert update_data['status'] == 'success'


@pytest.mark.integration
class TestMultiplePulls:
    """Test running POST /pull-data multiple times with overlapping data using real DB."""

    def test_multiple_pulls_with_overlapping_data(self, client, monkeypatch, fake_scraper_data, test_db_table):
        """Test that multiple pulls with overlapping data respect uniqueness (ON CONFLICT)."""

        setup_pull_data_mocks(monkeypatch, fake_scraper_data)

        # First pull - should insert all records
        response1 = client.post('/pull-data')
        assert response1.status_code == 200

        data1 = json.loads(response1.data)
        assert data1['inserted'] == 3
        assert data1['skipped'] == 0

        # Verify database state
        cursor = test_db_table.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_applicants;")
        count = cursor.fetchone()[0]
        assert count == 3
        cursor.close()

        # Second pull with same data - should skip all duplicates due to ON CONFLICT
        response2 = client.post('/pull-data')
        assert response2.status_code == 200

        data2 = json.loads(response2.data)
        assert data2['inserted'] == 0, "Second pull should not insert duplicates"
        assert data2['skipped'] == 3, "Second pull should skip all 3 duplicates"

        # Verify database still has only 3 records
        cursor = test_db_table.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_applicants;")
        count = cursor.fetchone()[0]
        assert count == 3, "Database should still have only 3 records"
        cursor.close()

    def test_partial_overlap_in_multiple_pulls(self, client, monkeypatch, fake_scraper_data, test_db_table):
        """Test multiple pulls with partially overlapping data."""

        monkeypatch.setattr('subprocess.run', lambda *_args, **_kwargs: MockSubprocessResult(returncode=0))
        monkeypatch.setattr('os.path.exists', lambda path: 'new_applicant_data.json' in str(path))
        monkeypatch.setattr('os.remove', lambda _path: None)

        # First pull with first 2 records
        first_batch = fake_scraper_data[:2]

        original_open = open
        def mock_open_first(path, *args, **kwargs):
            if 'new_applicant_data.json' in str(path):
                class MockFile:
                    def __enter__(self):
                        return self
                    def __exit__(self, *_args):
                        pass
                    def read(self):
                        return json.dumps(first_batch)
                return MockFile()
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr('builtins.open', mock_open_first)

        response1 = client.post('/pull-data')
        assert response1.status_code == 200

        data1 = json.loads(response1.data)
        assert data1['inserted'] == 2
        assert data1['skipped'] == 0

        # Second pull with last 2 records (1 overlap, 1 new)
        second_batch = fake_scraper_data[1:]

        def mock_open_second(path, *args, **kwargs):
            if 'new_applicant_data.json' in str(path):
                class MockFile:
                    def __enter__(self):
                        return self
                    def __exit__(self, *_args):
                        pass
                    def read(self):
                        return json.dumps(second_batch)
                return MockFile()
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr('builtins.open', mock_open_second)

        response2 = client.post('/pull-data')
        assert response2.status_code == 200

        data2 = json.loads(response2.data)
        assert data2['inserted'] == 1, "Should insert only the 1 new record"
        assert data2['skipped'] == 1, "Should skip the 1 duplicate"

        # Verify final database state
        cursor = test_db_table.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_applicants;")
        count = cursor.fetchone()[0]
        assert count == 3, "Database should have all 3 unique records"
        cursor.close()

    def test_consistency_after_multiple_pulls(self, client, monkeypatch, fake_scraper_data, test_db_table):
        """Test that database remains consistent after multiple pulls."""

        setup_pull_data_mocks(monkeypatch, fake_scraper_data)

        # Run pull 3 times with same data
        for i in range(3):
            response = client.post('/pull-data')
            assert response.status_code == 200

            data = json.loads(response.data)
            if i == 0:
                # First pull inserts all
                assert data['inserted'] == 3
            else:
                # Subsequent pulls skip all
                assert data['inserted'] == 0
                assert data['skipped'] == 3

        # Verify final consistency
        cursor = test_db_table.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_applicants;")
        count = cursor.fetchone()[0]
        assert count == 3

        # Verify no duplicate p_ids
        cursor.execute("SELECT p_id, COUNT(*) FROM test_applicants GROUP BY p_id HAVING COUNT(*) > 1;")
        duplicates = cursor.fetchall()
        assert len(duplicates) == 0, "Database should not contain duplicate p_ids"
        cursor.close()


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
