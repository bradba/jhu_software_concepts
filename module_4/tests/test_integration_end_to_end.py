"""
Integration Tests - End-to-End Workflow
Tests the complete workflow: pull data -> update analysis -> render page.
"""

import pytest
import sys
import os
import json
import re

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class MockSubprocessResult:
    """Mock object for subprocess.run() results."""
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class MockCursor:
    """Mock database cursor with persistent state."""
    def __init__(self, shared_state):
        self.executed_queries = []
        self.rowcount = 1
        self.closed = False
        self._shared_state = shared_state  # Shared state across connections
        self._inserted_data = self._shared_state['data']
        self._duplicate_check = self._shared_state['seen_ids']

    def execute(self, query, params=None):
        """Track executed queries and simulate ON CONFLICT behavior."""
        self.executed_queries.append((query, params))

        # Simulate INSERT with ON CONFLICT DO NOTHING
        if params and 'INSERT' in query and 'ON CONFLICT' in query:
            p_id = params[0]
            if p_id in self._duplicate_check:
                # Duplicate - ON CONFLICT DO NOTHING
                self.rowcount = 0
            else:
                # New record
                self._duplicate_check.add(p_id)
                self._inserted_data.append(params)
                self.rowcount = 1
        else:
            self.rowcount = 1

    def fetchall(self):
        """Return all inserted data as query results."""
        # Convert inserted data to dict format
        results = []
        for params in self._inserted_data:
            if len(params) >= 13:
                results.append({
                    'p_id': params[0],
                    'program': params[1],
                    'comments': params[2],
                    'date_added': params[3],
                    'url': params[4],
                    'status': params[5],
                    'term': params[6],
                    'us_or_international': params[7],
                    'gpa': params[8],
                    'gre': params[9],
                    'gre_v': params[10],
                    'gre_aw': params[11],
                    'degree': params[12],
                    'llm_generated_program': params[13] if len(params) > 13 else None,
                    'llm_generated_university': params[14] if len(params) > 14 else None
                })
        return results

    def close(self):
        """Close the cursor."""
        self.closed = True


class MockConnection:
    """Mock database connection with shared state."""
    def __init__(self, shared_state):
        self.committed = False
        self.closed = False
        self._shared_state = shared_state
        self._cursor = None

    def cursor(self):
        """Return a cursor with shared state."""
        self._cursor = MockCursor(self._shared_state)
        return self._cursor

    def commit(self):
        """Track commits."""
        self.committed = True

    def close(self):
        """Close the connection."""
        self.closed = True


@pytest.fixture
def shared_db_state():
    """Shared database state across all connections in a test."""
    return {
        'data': [],           # All inserted records
        'seen_ids': set()     # Set of p_ids for duplicate detection
    }


@pytest.fixture
def mock_query_functions(monkeypatch, shared_db_state):
    """Mock query_data functions with shared state."""
    def mock_get_connection():
        return MockConnection(shared_db_state)

    # Mock query functions with realistic return values
    monkeypatch.setattr('query_data.get_connection', mock_get_connection)
    monkeypatch.setattr('query_data.question_1', lambda _conn: len(shared_db_state['data']))
    monkeypatch.setattr('query_data.question_2', lambda _conn: 67.12)
    monkeypatch.setattr('query_data.question_3', lambda _conn: {
        'avg_gpa': 3.75,
        'avg_gre': 325.5,
        'avg_gre_v': 162.3,
        'avg_gre_aw': 4.2
    })
    monkeypatch.setattr('query_data.question_4', lambda _conn: 3.80)
    monkeypatch.setattr('query_data.question_5', lambda _conn: 45.68)
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


@pytest.fixture
def fake_scraper_data():
    """Fake scraper that returns multiple realistic records."""
    return [
        {
            'url': 'https://www.thegradcafe.com/survey/?p=101',
            'university': 'Stanford University',
            'program_name': 'Computer Science PhD',
            'comments': 'Great funding package',
            'date_posted': '01 Feb 2025',
            'applicant_status': 'Accepted',
            'start_term': 'Fall 2025',
            'citizenship': 'International',
            'gpa': '3.9',
            'gre_score': '330',
            'gre_v': '168',
            'gre_aw': '5.0',
            'degree': 'PhD'
        },
        {
            'url': 'https://www.thegradcafe.com/survey/?p=102',
            'university': 'MIT',
            'program_name': 'Computer Science PhD',
            'comments': 'Interview went well',
            'date_posted': '05 Feb 2025',
            'applicant_status': 'Accepted',
            'start_term': 'Fall 2025',
            'citizenship': 'American',
            'gpa': '3.8',
            'gre_score': '325',
            'gre_v': '165',
            'gre_aw': '4.5',
            'degree': 'PhD'
        },
        {
            'url': 'https://www.thegradcafe.com/survey/?p=103',
            'university': 'UC Berkeley',
            'program_name': 'Data Science MS',
            'comments': 'Quick response',
            'date_posted': '10 Feb 2025',
            'applicant_status': 'Rejected',
            'start_term': 'Fall 2025',
            'citizenship': 'International',
            'gpa': '3.7',
            'gre_score': '320',
            'gre_v': '162',
            'gre_aw': '4.0',
            'degree': 'Masters'
        }
    ]


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflow: pull -> update -> render."""

    def test_complete_workflow(self, client, monkeypatch, fake_scraper_data, shared_db_state):
        """Test full workflow: inject fake scraper, pull data, update analysis, render page."""

        # Step 1: Mock subprocess.run for scraper
        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Scraping complete')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: True)

        # Step 2: Mock file reading to return fake scraper data
        class MockFile:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                pass
            def read(self):
                return json.dumps(fake_scraper_data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())

        # Step 3: Mock load_data functions
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda url: url.split('=')[-1])
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # Step 4: POST /pull-data - should succeed and insert rows
        pull_response = client.post('/pull-data')
        assert pull_response.status_code == 200, "Pull data should succeed"

        pull_data = json.loads(pull_response.data)
        assert pull_data['status'] == 'success'
        assert pull_data['inserted'] == 3, "Should insert 3 records"
        assert pull_data['skipped'] == 0

        # Step 5: Verify rows are in the database
        assert len(shared_db_state['data']) == 3, "Database should contain 3 records"
        assert len(shared_db_state['seen_ids']) == 3, "Should have 3 unique IDs"

        # Verify the data content
        inserted_p_ids = {record[0] for record in shared_db_state['data']}
        assert '101' in inserted_p_ids
        assert '102' in inserted_p_ids
        assert '103' in inserted_p_ids

        # Step 6: POST /update-analysis - should succeed when not busy
        update_response = client.post('/update-analysis')
        assert update_response.status_code == 200, "Update analysis should succeed"

        update_data = json.loads(update_response.data)
        assert update_data['status'] == 'success'

        # Step 7: Restore normal file opening for template rendering
        monkeypatch.undo()  # Remove all monkeypatches to restore normal behavior

        # Re-apply only the necessary mocks for query functions
        def mock_get_connection_for_render():
            return MockConnection(shared_db_state)

        monkeypatch.setattr('query_data.get_connection', mock_get_connection_for_render)
        monkeypatch.setattr('query_data.question_1', lambda _conn: len(shared_db_state['data']))
        monkeypatch.setattr('query_data.question_2', lambda _conn: 67.12)
        monkeypatch.setattr('query_data.question_3', lambda _conn: {
            'avg_gpa': 3.75,
            'avg_gre': 325.5,
            'avg_gre_v': 162.3,
            'avg_gre_aw': 4.2
        })
        monkeypatch.setattr('query_data.question_4', lambda _conn: 3.80)
        monkeypatch.setattr('query_data.question_5', lambda _conn: 45.68)
        monkeypatch.setattr('query_data.question_6', lambda _conn: 3.85)
        monkeypatch.setattr('query_data.question_7', lambda _conn: 250)
        monkeypatch.setattr('query_data.question_8', lambda _conn: 45)
        monkeypatch.setattr('query_data.question_9', lambda _conn: [50, 45])
        monkeypatch.setattr('query_data.question_10', lambda _conn: [])
        monkeypatch.setattr('query_data.question_11', lambda _conn: [])

        # Now GET / (analysis page) - should render with correctly formatted values
        analysis_response = client.get('/')
        assert analysis_response.status_code == 200

        html_content = analysis_response.data.decode('utf-8')

        # Verify page contains Answer labels (if it's HTML, not JSON)
        if 'Answer:' in html_content:
            # Verify percentages are formatted with 2 decimals
            percentage_pattern = re.compile(r'(\d+\.\d+)%')
            percentages = percentage_pattern.findall(html_content)

            for percentage in percentages:
                decimal_part = percentage.split('.')[-1]
                assert len(decimal_part) == 2, \
                    f"Percentage {percentage}% should have exactly 2 decimal places"

            # Verify specific formatted percentages from our mock data
            assert '67.12' in html_content or '67.12%' in html_content
            assert '45.68' in html_content or '45.68%' in html_content

    def test_pull_data_inserts_all_records(self, client, monkeypatch, fake_scraper_data, shared_db_state):
        """Test that pull data successfully inserts all records from fake scraper."""

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
                return json.dumps(fake_scraper_data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda url: url.split('=')[-1])
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # Pull data
        response = client.post('/pull-data')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['inserted'] == len(fake_scraper_data)

        # Verify all records are in database
        assert len(shared_db_state['data']) == len(fake_scraper_data)

    def test_update_analysis_succeeds_after_pull(self, client, monkeypatch, fake_scraper_data, shared_db_state):
        """Test that update analysis succeeds after pulling data."""

        # First, pull data
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
                return json.dumps(fake_scraper_data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda url: url.split('=')[-1])
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        pull_response = client.post('/pull-data')
        assert pull_response.status_code == 200

        # Then, update analysis
        update_response = client.post('/update-analysis')
        assert update_response.status_code == 200

        update_data = json.loads(update_response.data)
        assert update_data['status'] == 'success'


@pytest.mark.integration
class TestMultiplePulls:
    """Test running POST /pull-data multiple times with overlapping data."""

    def test_multiple_pulls_with_overlapping_data(self, client, monkeypatch, fake_scraper_data, shared_db_state):
        """Test that multiple pulls with overlapping data respect uniqueness policy."""

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
                return json.dumps(fake_scraper_data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda url: url.split('=')[-1])
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # First pull - should insert all records
        response1 = client.post('/pull-data')
        assert response1.status_code == 200

        data1 = json.loads(response1.data)
        assert data1['inserted'] == 3
        assert data1['skipped'] == 0

        # Verify database state after first pull
        assert len(shared_db_state['data']) == 3
        assert len(shared_db_state['seen_ids']) == 3

        # Second pull with same data - should skip all duplicates
        response2 = client.post('/pull-data')
        assert response2.status_code == 200

        data2 = json.loads(response2.data)
        assert data2['inserted'] == 0, "Second pull should not insert duplicates"
        assert data2['skipped'] == 3, "Second pull should skip all 3 duplicates"

        # Verify database state hasn't changed
        assert len(shared_db_state['data']) == 3, "Database should still have only 3 records"
        assert len(shared_db_state['seen_ids']) == 3, "Should still have only 3 unique IDs"

    def test_partial_overlap_in_multiple_pulls(self, client, monkeypatch, fake_scraper_data, shared_db_state):
        """Test multiple pulls with partially overlapping data."""

        def mock_subprocess_run(*_args, **_kwargs):
            return MockSubprocessResult(returncode=0, stdout='Success')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('os.path.exists', lambda _path: True)
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda url: url.split('=')[-1])
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # First pull with first 2 records
        first_batch = fake_scraper_data[:2]

        class MockFile1:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                pass
            def read(self):
                return json.dumps(first_batch)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile1())

        response1 = client.post('/pull-data')
        assert response1.status_code == 200

        data1 = json.loads(response1.data)
        assert data1['inserted'] == 2
        assert data1['skipped'] == 0

        # Second pull with last 2 records (1 overlap, 1 new)
        second_batch = fake_scraper_data[1:]

        class MockFile2:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                pass
            def read(self):
                return json.dumps(second_batch)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile2())

        response2 = client.post('/pull-data')
        assert response2.status_code == 200

        data2 = json.loads(response2.data)
        assert data2['inserted'] == 1, "Should insert only the 1 new record"
        assert data2['skipped'] == 1, "Should skip the 1 duplicate"

        # Verify final database state
        assert len(shared_db_state['data']) == 3, "Database should have all 3 unique records"
        assert len(shared_db_state['seen_ids']) == 3

    def test_consistency_after_multiple_pulls(self, client, monkeypatch, fake_scraper_data, shared_db_state):
        """Test that database remains consistent after multiple pulls."""

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
                return json.dumps(fake_scraper_data)

        monkeypatch.setattr('builtins.open', lambda *_args, **_kwargs: MockFile())
        monkeypatch.setattr('load_data.extract_p_id_from_url', lambda url: url.split('=')[-1])
        monkeypatch.setattr('load_data.clean_string', lambda x: x if x else None)
        monkeypatch.setattr('load_data.parse_date', lambda _x: '2025-02-01')
        monkeypatch.setattr('os.remove', lambda _path: None)

        # Run pull 3 times with same data
        for i in range(3):
            response = client.post('/pull-data')
            assert response.status_code == 200

            if i == 0:
                # First pull inserts all
                data = json.loads(response.data)
                assert data['inserted'] == 3
            else:
                # Subsequent pulls skip all
                data = json.loads(response.data)
                assert data['inserted'] == 0
                assert data['skipped'] == 3

        # Verify final consistency
        assert len(shared_db_state['data']) == 3
        assert len(shared_db_state['seen_ids']) == 3

        # Verify no duplicate p_ids in data
        p_ids_in_data = [record[0] for record in shared_db_state['data']]
        assert len(p_ids_in_data) == len(set(p_ids_in_data)), \
            "Database should not contain duplicate p_ids"


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
