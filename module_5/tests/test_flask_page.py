"""
Unit tests for Flask application - Page Rendering and Routes
Tests the Flask app factory, configuration, and page rendering.
"""

import json
import os
import runpy
import sys
from unittest.mock import patch, MagicMock

import flask
import pytest

# Add src directory to path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def app():
    """
    Create and configure a test Flask application instance.
    Mocks database connections and query functions.
    """
    # Mock query_data module before importing app
    with patch('query_data.get_connection') as mock_conn, \
         patch('query_data.question_1') as mock_q1, \
         patch('query_data.question_2') as mock_q2, \
         patch('query_data.question_3') as mock_q3, \
         patch('query_data.question_4') as mock_q4, \
         patch('query_data.question_5') as mock_q5, \
         patch('query_data.question_6') as mock_q6, \
         patch('query_data.question_7') as mock_q7, \
         patch('query_data.question_8') as mock_q8, \
         patch('query_data.question_9') as mock_q9, \
         patch('query_data.question_10') as mock_q10, \
         patch('query_data.question_11') as mock_q11:

        # Setup mock return values
        mock_conn.return_value = MagicMock()
        mock_q1.return_value = 1500
        mock_q2.return_value = 50.25
        mock_q3.return_value = {
            'avg_gpa': 3.75,
            'avg_gre': 325.5,
            'avg_gre_v': 162.3,
            'avg_gre_aw': 4.2
        }
        mock_q4.return_value = 3.80
        mock_q5.return_value = 45.67
        mock_q6.return_value = 3.85
        mock_q7.return_value = 250
        mock_q8.return_value = 45
        mock_q9.return_value = [50, 45]
        mock_q10.return_value = [
            ('Stanford', 'Computer Science PhD', 120, 15, 12.5),
            ('MIT', 'Computer Science PhD', 110, 12, 10.9)
        ]
        mock_q11.return_value = [
            ('PhD', 500, 100, 20.0, 3.85, 80),
            ('Masters', 800, 520, 65.0, 3.75, 450)
        ]

        # Import app after mocking
        from app import app as flask_app

        # Configure for testing
        flask_app.config['TESTING'] = True
        flask_app.config['DEBUG'] = False

        yield flask_app


@pytest.fixture
def client(app):
    """
    Create a test client for the Flask application.
    """
    return app.test_client()


@pytest.mark.web
class TestAppFactory:
    """Test Flask app factory and configuration."""

    def test_app_creation(self, app):
        """Test that Flask app is created successfully."""
        assert app is not None
        assert app.config['TESTING'] is True

    def test_app_has_required_routes(self, app):
        """Test that the app has all required routes configured."""
        # Get all registered routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]

        # Check for required routes
        assert '/' in routes, "Main index route (/) should exist"
        assert '/pull-data' in routes, "Pull data route (/pull-data) should exist"

        # Verify static route exists (automatically added by Flask)
        assert '/static/<path:filename>' in routes

    def test_index_route_methods(self, app):
        """Test that index route accepts GET method."""
        rule = None
        for r in app.url_map.iter_rules():
            if r.rule == '/':
                rule = r
                break

        assert rule is not None
        assert 'GET' in rule.methods

    def test_pull_data_route_methods(self, app):
        """Test that pull-data route accepts POST method."""
        rule = None
        for r in app.url_map.iter_rules():
            if r.rule == '/pull-data':
                rule = r
                break

        assert rule is not None
        assert 'POST' in rule.methods


@pytest.mark.web
class TestAnalysisPageRendering:
    """Test GET /analysis (main index page) rendering and content."""

    def test_analysis_page_status_200(self, client):
        """Test that the analysis page loads successfully with status 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_page_contains_pull_data_button(self, client):
        """Test that page contains 'Pull Data' button."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check for Pull Data button text
        assert 'Pull Data' in html_content, "Page should contain 'Pull Data' button"

        # Check for button element with appropriate attributes
        assert 'pullDataBtn' in html_content or 'pull-data-btn' in html_content, \
            "Page should contain Pull Data button element"

    def test_page_contains_update_analysis_button(self, client):
        """Test that page contains 'Update Analysis' button."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check for Update Analysis button text
        assert 'Update Analysis' in html_content, "Page should contain 'Update Analysis' button"

        # Check for button element with appropriate attributes
        assert 'updateAnalysisBtn' in html_content or 'update-analysis-btn' in html_content, \
            "Page should contain Update Analysis button element"

    def test_page_text_includes_analysis(self, client):
        """Test that page text includes 'Analysis'."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check for "Analysis" text (case-sensitive)
        assert 'Analysis' in html_content, "Page text should include 'Analysis'"

    def test_page_text_includes_answer(self, client):
        """Test that page text includes at least one 'Answer:'."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check for "Answer:" text
        assert 'Answer:' in html_content, "Page text should include at least one 'Answer:'"

        # Verify multiple answers are present (since we have multiple questions)
        answer_count = html_content.count('Answer:')
        assert answer_count >= 1, f"Page should have at least 1 'Answer:', found {answer_count}"

    def test_page_has_valid_html_structure(self, client):
        """Test that page has valid HTML structure."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check for basic HTML structure
        assert '<!DOCTYPE html>' in html_content
        assert '<html' in html_content
        assert '<head>' in html_content
        assert '<body>' in html_content
        assert '</html>' in html_content

    def test_page_renders_query_results(self, client):
        """Test that page renders actual query results."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check that some of our mocked data appears in the page
        assert '1,500' in html_content or '1500' in html_content, \
            "Page should display the applicant count from question 1"
        assert '50.25' in html_content, \
            "Page should display percentage from question 2"


@pytest.mark.web
class TestPageContent:
    """Additional tests for page content and structure."""

    def test_page_title_contains_analysis(self, client):
        """Test that page title contains relevant content."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check for title tag with analysis-related content
        assert '<title>' in html_content
        assert 'Analysis' in html_content or 'Data' in html_content

    def test_control_panel_exists(self, client):
        """Test that data management control panel exists."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check for control panel elements
        assert 'control-panel' in html_content or 'Data Management' in html_content

    def test_page_contains_javascript_functions(self, client):
        """Test that page contains required JavaScript functions."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check for JavaScript functions
        assert 'pullNewData' in html_content, "Page should contain pullNewData() function"
        assert 'updateAnalysis' in html_content, "Page should contain updateAnalysis() function"


@pytest.mark.web
class TestIndexErrorHandling:
    """Test that index() returns 500 when database access fails (lines 220-222)."""

    def test_index_returns_500_on_database_error(self, client, monkeypatch):
        """index() catches any Exception from get_connection and returns 500."""
        def _fail():
            raise RuntimeError("Database unavailable")

        monkeypatch.setattr('query_data.get_connection', _fail)

        response = client.get('/')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'unavailable' in data['message'].lower()


@pytest.mark.web
class TestAppMainBlock:
    """Test app.py __main__ entry point."""

    def test_app_main(self, monkeypatch):
        """Test __main__ block by patching Flask.run to prevent server startup."""
        monkeypatch.setattr(flask.Flask, 'run', lambda self, **kwargs: None)
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')
        runpy.run_path(src_path, run_name='__main__')


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
