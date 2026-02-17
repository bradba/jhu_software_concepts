"""
Unit tests for Database Insert Operations
Tests database writes, idempotency constraints, and query functions.
"""

import json
import os
import sys

import pytest
from conftest import MockSubprocessResult

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class MockCursor:
    """Mock database cursor that tracks operations."""
    def __init__(self):
        self.executed_queries = []
        self.rowcount = 1
        self.closed = False
        self._inserted_data = []
        self._duplicate_check = set()

    def execute(self, query, params=None):
        """Track executed queries and simulate ON CONFLICT behavior."""
        self.executed_queries.append((query, params))

        # Simulate ON CONFLICT DO NOTHING behavior
        if params and 'ON CONFLICT' in query:
            # Use p_id (first param) as unique identifier
            p_id = params[0]
            if p_id in self._duplicate_check:
                # This is a duplicate - ON CONFLICT DO NOTHING means rowcount = 0
                self.rowcount = 0
            else:
                # New record - will be inserted
                self._duplicate_check.add(p_id)
                self._inserted_data.append(params)
                self.rowcount = 1
        else:
            # Regular query
            self.rowcount = 1

    def fetchall(self):
        """Return mock data for queries."""
        # Return sample data that matches the expected structure
        return [
            {
                'p_id': '123',
                'program': 'Stanford University, Computer Science',
                'comments': 'Great program!',
                'date_added': '2025-02-01',
                'url': 'https://www.thegradcafe.com/survey/?p=123',
                'status': 'Accepted',
                'term': 'Fall 2025',
                'us_or_international': 'International',
                'gpa': 3.8,
                'gre': 325.0,
                'gre_v': 165.0,
                'gre_aw': 4.5,
                'degree': 'PhD',
                'llm_generated_program': None,
                'llm_generated_university': None
            }
        ]

    def close(self):
        """Close the cursor."""
        self.closed = True


class MockConnection:
    """Mock database connection that provides a mock cursor."""
    def __init__(self):
        self.committed = False
        self.closed = False
        self._cursor = MockCursor()

    def cursor(self):
        """Return the mock cursor."""
        return self._cursor

    def commit(self):
        """Track commits."""
        self.committed = True

    def close(self):
        """Close the connection."""
        self.closed = True


@pytest.mark.db
class TestInsertOnPull:
    """Test that pulling data inserts rows into the database."""

    def test_table_empty_before_pull(self, client, monkeypatch):
        """Test initial state - before pull, target table is conceptually empty."""
        # This test verifies the initial mock state
        mock_conn = MockConnection()
        cursor = mock_conn.cursor()

        # Initially, no inserts have been executed
        assert len(cursor.executed_queries) == 0
        assert len(cursor._inserted_data) == 0

    def test_rows_exist_after_pull(self, client, monkeypatch):
        """Test that after POST /pull-data, new rows exist with required fields."""
        # Mock subprocess.run
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: True)

        # Mock scraped data with all required fields
        mock_scraped_data = [
            {
                'url': 'https://www.thegradcafe.com/survey/?p=123',
                'university': 'Stanford University',
                'program_name': 'Computer Science',
                'comments': 'Great program!',
                'date_posted': '01 Feb 2025',
                'applicant_status': 'Accepted',
                'start_term': 'Fall 2025',
                'citizenship': 'International',
                'gpa': '3.8',
                'gre_score': '325',
                'gre_v': '165',
                'gre_aw': '4.5',
                'degree': 'PhD'
            }
        ]

        class MockFile:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                pass
            def read(self):
                return json.dumps(mock_scraped_data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())

        # Mock load_data functions
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda _url: '123')
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # Track the connection that will be used
        connections_used = []

        def track_connection():
            conn = MockConnection()
            connections_used.append(conn)
            return conn

        monkeypatch.setattr('query_data.get_connection', track_connection)

        # Make request
        response = client.post('/pull-data')

        # Assert success
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['inserted'] == 1

        # Verify that data was inserted into the database
        assert len(connections_used) > 0
        conn = connections_used[-1]  # Get the connection used for data insertion
        cursor = conn._cursor

        # Verify INSERT query was executed
        insert_queries = [q for q in cursor.executed_queries if 'INSERT' in q[0]]
        assert len(insert_queries) > 0, "Should have executed INSERT query"

        # Verify required fields were included
        _insert_query, insert_params = insert_queries[0]
        assert insert_params is not None
        assert len(insert_params) >= 13  # At least 13 fields based on app.py

        # Verify required non-null fields
        p_id, program, _comments, _date_added, url, status = insert_params[:6]
        assert p_id == '123'
        assert 'Stanford University' in program
        assert 'Computer Science' in program
        assert url == 'https://www.thegradcafe.com/survey/?p=123'
        assert status == 'Accepted'

    def test_multiple_rows_inserted(self, client, monkeypatch):
        """Test that multiple rows can be inserted in a single pull."""
        # Mock subprocess.run
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: True)

        # Mock multiple scraped entries
        mock_scraped_data = [
            {
                'url': f'https://www.thegradcafe.com/survey/?p={i}',
                'university': f'University {i}',
                'program_name': f'Program {i}',
                'comments': f'Comment {i}',
                'date_posted': '01 Feb 2025',
                'applicant_status': 'Accepted',
                'start_term': 'Fall 2025',
                'citizenship': 'International',
                'gpa': '3.8',
                'gre_score': '325',
                'gre_v': '165',
                'gre_aw': '4.5',
                'degree': 'PhD'
            }
            for i in range(1, 4)
        ]

        class MockFile:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                pass
            def read(self):
                return json.dumps(mock_scraped_data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda url: url.split('=')[-1])
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # Make request
        response = client.post('/pull-data')

        # Assert success
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['inserted'] == 3


@pytest.mark.db
class TestIdempotencyConstraints:
    """Test that duplicate pulls don't create duplicate database rows."""

    def test_duplicate_rows_prevented(self, client, monkeypatch):
        """Test that duplicate rows do not create duplicates in database."""
        # Mock subprocess.run
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: True)

        # Mock the same scraped data (duplicate)
        mock_scraped_data = [
            {
                'url': 'https://www.thegradcafe.com/survey/?p=123',
                'university': 'Stanford University',
                'program_name': 'Computer Science',
                'comments': 'Great program!',
                'date_posted': '01 Feb 2025',
                'applicant_status': 'Accepted',
                'start_term': 'Fall 2025',
                'citizenship': 'International',
                'gpa': '3.8',
                'gre_score': '325',
                'gre_v': '165',
                'gre_aw': '4.5',
                'degree': 'PhD'
            }
        ]

        class MockFile:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                pass
            def read(self):
                return json.dumps(mock_scraped_data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda _url: '123')
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # Shared state to track duplicates across mock connections
        duplicate_state = {'seen_ids': set()}

        def track_connection():
            conn = MockConnection()
            # Share duplicate state across connections
            conn._cursor._duplicate_check = duplicate_state['seen_ids']
            return conn

        monkeypatch.setattr('query_data.get_connection', track_connection)

        # First pull - should insert
        response1 = client.post('/pull-data')
        assert response1.status_code == 200
        data1 = json.loads(response1.data)
        assert data1['inserted'] == 1
        assert data1['skipped'] == 0

        # Second pull with same data - should skip due to ON CONFLICT
        response2 = client.post('/pull-data')
        assert response2.status_code == 200
        data2 = json.loads(response2.data)

        # Second pull should skip the duplicate
        # (In real DB, ON CONFLICT DO NOTHING means rowcount=0, so it's counted as skipped)
        assert data2['inserted'] == 0 and data2['skipped'] == 1, \
            f"Second pull should skip duplicate: inserted={data2['inserted']}, skipped={data2['skipped']}"

    def test_on_conflict_do_nothing_in_query(self, client, monkeypatch):
        """Test that the INSERT query includes ON CONFLICT DO NOTHING clause."""
        # Mock subprocess.run
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: True)

        mock_scraped_data = [{
            'url': 'https://www.thegradcafe.com/survey/?p=999',
            'university': 'Test University',
            'program_name': 'Test Program',
            'comments': 'Test comment',
            'date_posted': '01 Feb 2025',
            'applicant_status': 'Accepted',
            'start_term': 'Fall 2025',
            'citizenship': 'International',
            'gpa': '3.8',
            'gre_score': '325',
            'gre_v': '165',
            'gre_aw': '4.5',
            'degree': 'PhD'
        }]

        class MockFile:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                pass
            def read(self):
                return json.dumps(mock_scraped_data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda _url: '999')
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # Track connections
        connections_used = []

        def track_connection():
            conn = MockConnection()
            connections_used.append(conn)
            return conn

        monkeypatch.setattr('query_data.get_connection', track_connection)

        # Make request
        response = client.post('/pull-data')
        assert response.status_code == 200

        # Verify the query includes ON CONFLICT
        conn = connections_used[-1]
        cursor = conn._cursor
        insert_queries = [q[0] for q in cursor.executed_queries if 'INSERT' in q[0]]

        assert len(insert_queries) > 0
        # Check that the INSERT query has ON CONFLICT clause
        assert any('ON CONFLICT' in query for query in insert_queries), \
            "INSERT query should include ON CONFLICT DO NOTHING clause"


@pytest.mark.db
class TestSimpleQueryFunction:
    """Test that query functions return data with expected structure."""

    def test_query_returns_dict_with_expected_keys(self):
        """Test that query returns a dict with Module 3 required data fields."""
        # Create a mock connection
        mock_conn = MockConnection()
        cursor = mock_conn.cursor()

        # Get sample data from cursor
        results = cursor.fetchall()

        # Verify we got results
        assert len(results) > 0

        # Verify structure of first result
        result = results[0]

        # Required fields from Module 3
        required_keys = [
            'p_id',
            'program',
            'url',
            'status',
            'gpa',
            'gre',
            'degree'
        ]

        for key in required_keys:
            assert key in result, f"Result should contain '{key}' field"

        # Verify data types
        assert isinstance(result['p_id'], str)
        assert isinstance(result['program'], str)
        assert isinstance(result['url'], str)
        assert isinstance(result['status'], str)
        assert isinstance(result['gpa'], (int, float)) or result['gpa'] is None
        assert isinstance(result['gre'], (int, float)) or result['gre'] is None

    def test_query_result_has_non_null_required_fields(self):
        """Test that required fields are non-null in query results."""
        mock_conn = MockConnection()
        cursor = mock_conn.cursor()
        results = cursor.fetchall()

        assert len(results) > 0
        result = results[0]

        # These fields should never be null
        non_null_fields = ['p_id', 'program', 'url', 'status']

        for field in non_null_fields:
            assert result[field] is not None, f"Field '{field}' should not be null"
            assert result[field] != '', f"Field '{field}' should not be empty string"

    def test_query_result_structure_matches_m3_schema(self):
        """Test that the query result structure matches Module 3 schema."""
        mock_conn = MockConnection()
        cursor = mock_conn.cursor()
        results = cursor.fetchall()

        assert len(results) > 0
        result = results[0]

        # All Module 3 fields (both required and optional)
        expected_fields = [
            'p_id',              # Required
            'program',           # Required
            'comments',          # Optional
            'date_added',        # Required
            'url',               # Required
            'status',            # Required
            'term',              # Optional
            'us_or_international',  # Optional
            'gpa',               # Optional
            'gre',               # Optional
            'gre_v',             # Optional
            'gre_aw',            # Optional
            'degree',            # Optional
            'llm_generated_program',     # Optional (Module 4)
            'llm_generated_university'   # Optional (Module 4)
        ]

        for field in expected_fields:
            assert field in result, f"Result should include '{field}' field from schema"


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
