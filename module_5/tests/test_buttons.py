"""
Unit tests for Button Endpoints and Busy-State Behavior
Tests the POST endpoints for pull-data and update-analysis, including busy-state gating.
"""

import pytest
import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class MockSubprocessResult:
    """Mock object for subprocess.run() results."""
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class MockConnection:
    """Mock database connection."""
    def __init__(self):
        self.committed = False
        self.closed = False
        self._cursor = None

    def cursor(self):
        if self._cursor is None:
            self._cursor = MockCursor()
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


class MockCursor:
    """Mock database cursor."""
    def __init__(self):
        self.rowcount = 1
        self.executed_queries = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed_queries.append((query, params))

    def close(self):
        self.closed = True


@pytest.fixture
def mock_query_functions(monkeypatch):
    """Mock all query_data functions."""
    def mock_get_connection():
        return MockConnection()

    monkeypatch.setattr('query_data.get_connection', mock_get_connection)
    monkeypatch.setattr('query_data.question_1', lambda _conn: 1500)
    monkeypatch.setattr('query_data.question_2', lambda _conn: 50.25)
    monkeypatch.setattr('query_data.question_3', lambda _conn: {'avg_gpa': 3.75, 'avg_gre': 325.5})
    monkeypatch.setattr('query_data.question_4', lambda _conn: 3.80)
    monkeypatch.setattr('query_data.question_5', lambda _conn: 45.67)
    monkeypatch.setattr('query_data.question_6', lambda _conn: 3.85)
    monkeypatch.setattr('query_data.question_7', lambda _conn: 250)
    monkeypatch.setattr('query_data.question_8', lambda _conn: 45)
    monkeypatch.setattr('query_data.question_9', lambda _conn: [50, 45])
    monkeypatch.setattr('query_data.question_10', lambda _conn: [])
    monkeypatch.setattr('query_data.question_11', lambda _conn: [])


@pytest.fixture
def app(mock_query_functions):
    """Create and configure a test Flask application instance."""
    from app import app as flask_app

    flask_app.config['TESTING'] = True
    flask_app.config['DEBUG'] = False

    return flask_app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.mark.buttons
class TestPullDataEndpoint:
    """Test POST /pull-data endpoint behavior."""

    def test_pull_data_returns_200(self, client, monkeypatch):
        """Test that POST /pull-data returns 200 on success."""
        # Mock subprocess.run
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)

        # Mock os.path.exists
        monkeypatch.setattr('os.path.exists', lambda _path: True)

        # Mock file reading
        mock_scraped_data = [
            {
                'url': 'https://www.thegradcafe.com/survey/?p=123',
                'university': 'Stanford',
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
            def __init__(self, data):
                self.data = data

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                pass

            def read(self):
                return json.dumps(self.data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile(mock_scraped_data))

        # Mock load_data functions
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda _url: '123')
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')

        # Mock os.remove
        monkeypatch.setattr('os.remove', lambda _path: None)

        # Make request
        response = client.post('/pull-data')

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'inserted' in data

    def test_pull_data_triggers_loader(self, client, monkeypatch):
        """Test that POST /pull-data triggers the loader with scraped rows."""
        call_count = {'subprocess': 0, 'cursor_execute': 0}

        # Mock subprocess.run and count calls
        def mock_subprocess_run(*_args, **_kwargs):
            call_count['subprocess'] += 1
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

        # Mock load_data functions
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda url: url.split('=')[-1])
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # Mock database cursor to count execute calls
        original_cursor_class = MockCursor

        class CountingMockCursor(original_cursor_class):
            def execute(self, query, params=None):
                call_count['cursor_execute'] += 1
                super().execute(query, params)

        class CountingMockConnection(MockConnection):
            def cursor(self):
                return CountingMockCursor()

        monkeypatch.setattr('query_data.get_connection', lambda: CountingMockConnection())

        # Make request
        response = client.post('/pull-data')

        # Assert that scraper was called
        assert call_count['subprocess'] == 1

        # Assert that loader processed the data
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['inserted'] == 3  # All 3 entries inserted

        # Verify database inserts were attempted
        assert call_count['cursor_execute'] == 3


@pytest.mark.buttons
class TestUpdateAnalysisEndpoint:
    """Test POST /update-analysis endpoint behavior."""

    def test_update_analysis_returns_200_when_not_busy(self, client, monkeypatch):
        """Test that POST /update-analysis returns 200 when not busy."""
        # Mock the LLM update script to succeed
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('app.is_busy', lambda: False)

        # Make request
        response = client.post('/update-analysis')

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'


@pytest.mark.buttons
class TestBusyStateGating:
    """Test busy-state behavior for both endpoints."""

    def test_update_analysis_returns_409_when_pull_in_progress(self, client, monkeypatch):
        """Test that POST /update-analysis returns 409 when a pull is in progress."""
        # Simulate busy state
        monkeypatch.setattr('app.is_busy', lambda: True)

        response = client.post('/update-analysis')

        # Assert 409 Conflict
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['status'] in ['busy', 'error']
        message_lower = data.get('message', '').lower()
        assert 'busy' in message_lower or 'progress' in message_lower

    def test_pull_data_returns_409_when_busy(self, client, monkeypatch):
        """Test that POST /pull-data returns 409 when another operation is in progress."""
        # Simulate busy state
        monkeypatch.setattr('app.is_busy', lambda: True)

        response = client.post('/pull-data')

        # Assert 409 Conflict
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['status'] in ['busy', 'error']
        message_lower = data.get('message', '').lower()
        assert 'busy' in message_lower or 'progress' in message_lower

    def test_concurrent_operations_blocked(self, client, monkeypatch):
        """Test that operations are properly blocked when system is busy."""
        # Simulate busy state
        monkeypatch.setattr('app.is_busy', lambda: True)

        # Both should return 409
        pull_response = client.post('/pull-data')
        update_response = client.post('/update-analysis')

        assert pull_response.status_code == 409
        assert update_response.status_code == 409


@pytest.mark.buttons
class TestUpdateAnalysisEndpointWithLLM:
    """Test POST /update-analysis with LLM processing."""

    def test_update_analysis_calls_llm_script(self, client, monkeypatch):
        """Test that /update-analysis calls the LLM processing script."""
        call_count = {'subprocess': 0}

        # Mock successful LLM script execution and count calls
        def mock_subprocess_run(*_args, **_kwargs):
            call_count['subprocess'] += 1
            return MockSubprocessResult(returncode=0, stdout='Updated 10 entries')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('app.is_busy', lambda: False)

        # Make request
        response = client.post('/update-analysis')

        # Should succeed
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'

        # Verify subprocess was called (LLM script)
        assert call_count['subprocess'] == 1

    def test_update_analysis_handles_llm_failure(self, client, monkeypatch):
        """Test that /update-analysis handles LLM script failures gracefully."""
        # Mock failed LLM script execution
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=1, stderr='LLM API error')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('app.is_busy', lambda: False)

        # Make request
        response = client.post('/update-analysis')

        # Should return error status
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'


@pytest.mark.buttons
class TestBusyStateManagement:
    """Test busy-state flag management."""

    def test_busy_state_prevents_concurrent_pulls(self, client, monkeypatch):
        """Test that busy state prevents concurrent pull operations."""
        monkeypatch.setattr('app.is_busy', lambda: True)

        response1 = client.post('/pull-data')
        response2 = client.post('/pull-data')

        # Both should be rejected
        assert response1.status_code == 409
        assert response2.status_code == 409

    def test_busy_state_prevents_concurrent_updates(self, client, monkeypatch):
        """Test that busy state prevents concurrent update operations."""
        monkeypatch.setattr('app.is_busy', lambda: True)

        response1 = client.post('/update-analysis')
        response2 = client.post('/update-analysis')

        # Both should be rejected
        assert response1.status_code == 409
        assert response2.status_code == 409

    def test_operations_allowed_when_not_busy(self, client, monkeypatch):
        """Test that operations are allowed when system is not busy."""
        # Mock all dependencies
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        mock_scraped_data = [{
            'url': 'https://test.com/?p=1',
            'university': 'Test',
            'program_name': 'Test',
            'comments': None,
            'date_posted': '01 Feb',
            'applicant_status': 'Accepted',
            'start_term': 'Fall',
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

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: True)
        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda _url: '1')
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)
        monkeypatch.setattr('app.is_busy', lambda: False)

        # Both should succeed (200)
        pull_response = client.post('/pull-data')
        assert pull_response.status_code == 200


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
