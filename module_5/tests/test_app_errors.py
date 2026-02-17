"""
Unit tests for app.py error paths and edge cases
Tests error handling in Flask endpoints to achieve 100% coverage.
"""

import json
import os
import subprocess
import sys
from contextlib import contextmanager

import pytest
from conftest import MockSubprocessResult

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import app as app_module
from app import busy_state, _busy_lock


@pytest.mark.buttons
class TestPullDataErrorPaths:
    """Test error paths in POST /pull-data endpoint."""

    def test_scraper_fails_with_nonzero_returncode(self, client, monkeypatch):
        """Test that scraper failure returns 500 error."""
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=1, stderr='Scraper error')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)

        response = client.post('/pull-data')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Scraping failed' in data['message']

    def test_scraper_completes_but_no_file_created(self, client, monkeypatch):
        """Test error when scraper completes but doesn't create output file."""
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: False)

        response = client.post('/pull-data')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'No data file created by scraper' in data['message']

    def test_empty_scraped_data_returns_warning(self, client, monkeypatch):
        """Test that empty scraped data returns warning status."""
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: True)

        class MockFile:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                pass

            def read(self):
                return json.dumps([])  # Empty list

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())

        response = client.post('/pull-data')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'warning'
        assert 'No new entries found' in data['message']
        assert data['count'] == 0

    def test_p_id_extraction_fails(self, client, monkeypatch):
        """Test handling when p_id extraction fails for an entry."""
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: True)

        mock_scraped_data = [
            {
                'url': 'https://invalid-url.com',  # Will fail p_id extraction
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
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda _url: None)  # Fails
        monkeypatch.setattr('os.remove', lambda _path: None)

        response = client.post('/pull-data')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['inserted'] == 0
        assert data['skipped'] == 1

    def test_scraper_timeout(self, client, monkeypatch):
        """Test that scraper timeout returns 500 error."""
        def mock_subprocess_run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired('scrape.py', 300)

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)

        response = client.post('/pull-data')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'timed out' in data['message'].lower()


@pytest.mark.buttons
class TestUpdateAnalysisErrorPaths:
    """Test error paths in POST /update-analysis endpoint."""

    def test_llm_script_fails(self, client, monkeypatch):
        """Test that LLM script failure returns 500 error."""
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=1, stderr='LLM API error')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('app.is_busy', lambda: False)

        response = client.post('/update-analysis')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'failed' in data['message'].lower()

    def test_llm_script_timeout(self, client, monkeypatch):
        """Test that LLM script timeout returns 500 error."""
        def mock_subprocess_run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired('update_llm.py', 300)

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('app.is_busy', lambda: False)

        response = client.post('/update-analysis')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'timed out' in data['message'].lower()

    def test_llm_script_generic_error(self, client, monkeypatch):
        """Test generic error handling in update-analysis."""
        def mock_subprocess_run(*_args, **_kwargs):
            raise ValueError("Unexpected error")

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('app.is_busy', lambda: False)

        response = client.post('/update-analysis')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Error updating analysis' in data['message']


@pytest.mark.buttons
class TestBusyStateRuntimeError:
    """Test RuntimeError when busy state is already acquired."""

    def test_busy_state_context_manager_raises_on_double_acquisition(self):
        """Test that busy_state context manager raises RuntimeError if already busy."""
        # Manually set busy state
        with _busy_lock:
            app_module._is_busy = True

        try:
            # Try to acquire busy state again - should raise RuntimeError
            with busy_state():
                pass
        except RuntimeError as e:
            assert "already busy" in str(e).lower()
        finally:
            # Clean up
            with _busy_lock:
                app_module._is_busy = False

    def test_update_analysis_runtime_error(self, client, monkeypatch):
        """Test update-analysis handling of RuntimeError from busy_state."""
        @contextmanager
        def mock_busy_state():
            raise RuntimeError("System is already busy")
            yield  # pylint: disable=unreachable

        monkeypatch.setattr('app.busy_state', mock_busy_state)
        monkeypatch.setattr('app.is_busy', lambda: False)

        response = client.post('/update-analysis')

        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['status'] == 'busy'


@pytest.mark.buttons
class TestAdditionalPullDataErrors:
    """Test additional error paths in pull-data endpoint."""

    def test_pull_data_database_insert_error(self, client, tmp_path, monkeypatch, capsys):
        """Test pull-data handling of database insert errors."""
        # Create temporary JSON file with valid data
        json_file = tmp_path / "new_applicant_data.json"
        json_data = [{
            "url": "https://www.thegradcafe.com/survey/result/999999",
            "university": "Test University",
            "program_name": "Computer Science",
            "applicant_status": "Accepted",
            "start_term": "Fall 2026",
            "citizenship": "International",
            "gpa": "3.8",
            "gre_score": "325",
            "gre_v": "165",
            "gre_aw": "4.5",
            "degree": "PhD"
        }]
        json_file.write_text(json.dumps(json_data))

        # Mock scrape subprocess to succeed
        class MockSubprocessResult:
            returncode = 0
            stderr = ''

        def mock_subprocess_run(*args, **kwargs):
            return MockSubprocessResult()

        # Mock cursor to raise exception on execute
        class MockCursor:
            def execute(self, query, params=None):
                raise RuntimeError("Database insert failed")
            def close(self):
                pass
            rowcount = 0

        class MockConnection:
            def cursor(self):
                return MockCursor()
            def commit(self):
                pass
            def close(self):
                pass

        def mock_get_connection():
            return MockConnection()

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('query_data.get_connection', mock_get_connection)
        monkeypatch.setattr('os.path.exists', lambda x: x.endswith('new_applicant_data.json'))

        # Mock open to return our test file
        original_open = open
        def mock_open(path, *args, **kwargs):
            if 'new_applicant_data.json' in str(path):
                return json_file.open(*args, **kwargs)
            return original_open(path, *args, **kwargs)
        monkeypatch.setattr('builtins.open', mock_open)

        response = client.post('/pull-data')

        # Should succeed but with all entries skipped due to errors
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['skipped'] >= 1

        # Check error message was printed
        captured = capsys.readouterr()
        assert 'Error processing entry' in captured.out

    def test_pull_data_file_removal_error(self, client, tmp_path, monkeypatch):
        """Test pull-data when file removal fails (bare except)."""
        json_file = tmp_path / "new_applicant_data.json"
        json_data = [{
            "url": "https://www.thegradcafe.com/survey/result/888888",
            "university": "Test Univ",
            "program_name": "CS",
            "degree": "PhD"
        }]
        json_file.write_text(json.dumps(json_data))

        class MockSubprocessResult:
            returncode = 0
            stderr = ''

        def mock_subprocess_run(*args, **kwargs):
            return MockSubprocessResult()

        class MockCursor:
            def __init__(self):
                self.rowcount = 1
            def execute(self, query, params=None):
                pass
            def close(self):
                pass

        class MockConnection:
            def cursor(self):
                return MockCursor()
            def commit(self):
                pass
            def close(self):
                pass

        def mock_get_connection():
            return MockConnection()

        def mock_remove(path):
            raise OSError("Permission denied - cannot remove file")

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('query_data.get_connection', mock_get_connection)
        monkeypatch.setattr('os.path.exists', lambda x: x.endswith('new_applicant_data.json'))

        original_open = open
        def mock_open(path, *args, **kwargs):
            if 'new_applicant_data.json' in str(path):
                return json_file.open(*args, **kwargs)
            return original_open(path, *args, **kwargs)
        monkeypatch.setattr('builtins.open', mock_open)
        monkeypatch.setattr('os.remove', mock_remove)

        response = client.post('/pull-data')

        # Should still succeed even if file removal fails (bare except catches it)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'

    def test_pull_data_generic_exception(self, client, monkeypatch):
        """Test pull-data handling of generic exceptions."""
        # Mock busy_state to raise a generic exception
        @contextmanager
        def mock_busy_state():
            raise ValueError("Unexpected error in busy state")
            yield  # pylint: disable=unreachable

        monkeypatch.setattr('app.busy_state', mock_busy_state)
        monkeypatch.setattr('app.is_busy', lambda: False)

        response = client.post('/pull-data')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'

    def test_pull_data_runtime_error_from_context_manager(self, client, monkeypatch):
        """Test pull-data handling of RuntimeError from busy_state context manager."""
        # Mock busy_state to raise RuntimeError
        @contextmanager
        def mock_busy_state():
            raise RuntimeError("System is already busy")
            yield  # pylint: disable=unreachable

        monkeypatch.setattr('app.busy_state', mock_busy_state)
        monkeypatch.setattr('app.is_busy', lambda: False)

        response = client.post('/pull-data')

        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['status'] == 'busy'


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
