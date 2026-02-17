"""Shared pytest fixtures and mock classes for the test suite."""

import os
import sys

import pytest

# Add src and tests directories to path so all test files can import from both
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))


class MockSubprocessResult:
    """Mock object for subprocess.run() results."""

    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class MockConnection:
    """Simple mock database connection (cursor returns self)."""

    def __init__(self):
        self.committed = False
        self.closed = False

    def cursor(self):
        """Return self as the cursor (combined connection/cursor mock)."""
        return self

    rowcount = 1

    def execute(self, *_args, **_kwargs):
        """Accept any query execution without action."""

    def fetchone(self):
        """Return None for all fetchone calls."""
        return None

    def fetchall(self):
        """Return empty list for all fetchall calls."""
        return []

    def commit(self):
        """Record that a commit was made."""
        self.committed = True

    def close(self):
        """Record that the connection was closed."""
        self.closed = True


@pytest.fixture
def mock_query_functions(monkeypatch):
    """Mock all query_data functions with default return values."""
    def mock_get_connection():
        return MockConnection()

    monkeypatch.setattr('query_data.get_connection', mock_get_connection)
    monkeypatch.setattr('query_data.question_1', lambda _conn: 1500)
    monkeypatch.setattr('query_data.question_2', lambda _conn: 50.25)
    monkeypatch.setattr('query_data.question_3', lambda _conn: {
        'avg_gpa': 3.75,
        'avg_gre': 325.5,
        'avg_gre_v': 162.3,
        'avg_gre_aw': 4.2,
    })
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
