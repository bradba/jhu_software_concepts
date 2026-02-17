"""
Unit tests for scrape.py web scraping functions
Tests URL fetching, HTML parsing, and data extraction.
"""

import pytest
import sys
import os
import json
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import scrape


@pytest.mark.integration
class TestFetchURL:
    """Test URL fetching function."""

    def test_fetch_url_successful(self, monkeypatch):
        """Test successful URL fetch."""
        class MockResponse:
            status = 200
            data = b'<html><body>Test</body></html>'

        class MockHTTP:
            def request(self, method, url, headers=None):
                return MockResponse()

        monkeypatch.setattr('scrape._http', MockHTTP())
        monkeypatch.setattr('time.sleep', lambda x: None)  # Skip sleep

        result = scrape._fetch_url('https://test.com')

        assert result == '<html><body>Test</body></html>'

    def test_fetch_url_with_error_status(self, monkeypatch, capsys):
        """Test URL fetch with error status."""
        class MockResponse:
            status = 404
            data = b''

        class MockHTTP:
            def request(self, method, url, headers=None):
                return MockResponse()

        monkeypatch.setattr('scrape._http', MockHTTP())
        monkeypatch.setattr('time.sleep', lambda x: None)

        result = scrape._fetch_url('https://test.com')

        assert result is None

        # Check error message
        captured = capsys.readouterr()
        assert '404' in captured.out


@pytest.mark.integration
class TestExtractCommentsFromResultPage:
    """Test comment extraction from result pages."""

    def test_extract_comments_with_notes_field(self, monkeypatch):
        """Test extracting comments when Notes field exists."""
        html_content = '''
        <html>
            <dt>Notes</dt>
            <dd>This is a great program with excellent faculty!</dd>
        </html>
        '''

        def mock_fetch(url):
            return html_content

        monkeypatch.setattr('scrape._fetch_url', mock_fetch)

        result = scrape._extract_comments_from_result_page('https://test.com')

        assert result == 'This is a great program with excellent faculty!'

    def test_extract_comments_with_comments_field(self, monkeypatch):
        """Test extracting from Comments field."""
        html_content = '''
        <html>
            <dt>Comments</dt>
            <dd>Amazing experience!</dd>
        </html>
        '''

        def mock_fetch(url):
            return html_content

        monkeypatch.setattr('scrape._fetch_url', mock_fetch)

        result = scrape._extract_comments_from_result_page('https://test.com')

        assert result == 'Amazing experience!'

    def test_extract_comments_no_field(self, monkeypatch):
        """Test when no comments field exists."""
        html_content = '<html><body>No comments here</body></html>'

        def mock_fetch(url):
            return html_content

        monkeypatch.setattr('scrape._fetch_url', mock_fetch)

        result = scrape._extract_comments_from_result_page('https://test.com')

        assert result is None

    def test_extract_comments_fetch_fails(self, monkeypatch):
        """Test when URL fetch fails."""
        def mock_fetch(url):
            return None

        monkeypatch.setattr('scrape._fetch_url', mock_fetch)

        result = scrape._extract_comments_from_result_page('https://test.com')

        assert result is None


@pytest.mark.integration
class TestExtractEntriesFromPage:
    """Test entry extraction from HTML table."""

    def test_extract_entries_from_valid_html(self, monkeypatch):
        """Test extracting entries from valid HTML table."""
        html_content = '''
        <html><body>
        <table>
            <tr><th>Header</th></tr>
            <tr>
                <td>Stanford University</td>
                <td><span>Computer Science</span><span>PhD</span></td>
                <td>01 Feb 2026</td>
                <td>Accepted on 28 Jan</td>
                <td><a href="/result/123">View</a></td>
            </tr>
            <tr>
                <td colspan="5">Fall 2026 International GPA 3.8 GRE 325 GRE V 165 AW 4.5</td>
            </tr>
        </table>
        </body></html>
        '''

        # Mock the comment extraction to avoid network calls
        monkeypatch.setattr('scrape._extract_comments_from_result_page', lambda url: None)

        result = scrape._extract_entries_from_page(html_content, 'https://test.com')

        assert len(result) == 1
        entry = result[0]
        assert entry['university'] == 'Stanford University'
        assert entry['program_name'] == 'Computer Science'
        assert entry['degree'] == 'PhD'
        assert entry['applicant_status'] == 'Accepted'
        assert entry['start_term'] == 'Fall 2026'
        assert entry['citizenship'] == 'International'
        assert entry['gpa'] == '3.8'
        assert entry['gre_score'] == '325'
        assert entry['gre_v'] == '165'
        assert entry['gre_aw'] == '4.5'

    def test_extract_entries_with_rejection(self, monkeypatch):
        """Test extracting rejected entry."""
        html_content = '''
        <html><body>
        <table>
            <tr><th>Header</th></tr>
            <tr>
                <td>MIT</td>
                <td><span>Electrical Engineering</span><span>Masters</span></td>
                <td>15 Jan 2026</td>
                <td>Rejected on 10 Jan</td>
                <td></td>
            </tr>
        </table>
        </body></html>
        '''

        monkeypatch.setattr('scrape._extract_comments_from_result_page', lambda url: None)

        result = scrape._extract_entries_from_page(html_content, 'https://test.com')

        assert len(result) == 1
        assert result[0]['applicant_status'] == 'Rejected'
        assert result[0]['rejected_date'] == '10 Jan'

    def test_extract_entries_with_american_citizenship(self, monkeypatch):
        """Test extracting entry with American citizenship."""
        html_content = '''
        <html><body>
        <table>
            <tr><th>Header</th></tr>
            <tr>
                <td>CMU</td>
                <td><span>CS</span><span>PhD</span></td>
                <td>01 Feb</td>
                <td>Accepted</td>
                <td></td>
            </tr>
            <tr>
                <td colspan="5">Spring 2026 American</td>
            </tr>
        </table>
        </body></html>
        '''

        monkeypatch.setattr('scrape._extract_comments_from_result_page', lambda url: None)

        result = scrape._extract_entries_from_page(html_content, 'https://test.com')

        assert len(result) == 1
        assert result[0]['citizenship'] == 'American'

    def test_extract_entries_no_table(self):
        """Test with HTML that has no table."""
        html_content = '<html><body>No table here</body></html>'

        result = scrape._extract_entries_from_page(html_content, 'https://test.com')

        assert result == []

    def test_extract_entries_with_rich_comments(self, monkeypatch):
        """Test extracting entries with rich comments from result page."""
        html_content = '''
        <html><body>
        <table>
            <tr><th>Header</th></tr>
            <tr>
                <td>Stanford</td>
                <td><span>CS</span><span>PhD</span></td>
                <td>01 Feb</td>
                <td>Accepted</td>
                <td><a href="/result/999">View</a></td>
            </tr>
        </table>
        </body></html>
        '''

        def mock_extract_comments(url):
            if '999' in url:
                return "Detailed comments from result page!"
            return None

        monkeypatch.setattr('scrape._extract_comments_from_result_page', mock_extract_comments)

        result = scrape._extract_entries_from_page(html_content, 'https://test.com')

        assert len(result) == 1
        assert result[0]['comments'] == "Detailed comments from result page!"


@pytest.mark.integration
class TestScrapeData:
    """Test main scraping function."""

    def test_scrape_data_with_limit(self, monkeypatch, capsys):
        """Test scraping with entry limit."""
        page_html = '''
        <html><body>
        <table>
            <tr><th>Header</th></tr>
            <tr>
                <td>Univ1</td>
                <td><span>Program1</span><span>PhD</span></td>
                <td>Date1</td>
                <td>Accepted</td>
                <td></td>
            </tr>
            <tr>
                <td>Univ2</td>
                <td><span>Program2</span><span>Masters</span></td>
                <td>Date2</td>
                <td>Rejected</td>
                <td></td>
            </tr>
        </table>
        </body></html>
        '''

        def mock_fetch(url):
            return page_html

        monkeypatch.setattr('scrape._fetch_url', mock_fetch)
        monkeypatch.setattr('scrape._extract_comments_from_result_page', lambda url: None)

        result = scrape.scrape_data(limit=3)

        # Should stop after collecting 3 entries (needs 2 pages)
        assert len(result) == 3

        # Check console output
        captured = capsys.readouterr()
        assert 'collected' in captured.out

    def test_scrape_data_stops_on_failed_fetch(self, monkeypatch, capsys):
        """Test scraping stops when fetch fails."""
        def mock_fetch(url):
            return None  # Simulate fetch failure

        monkeypatch.setattr('scrape._fetch_url', mock_fetch)

        result = scrape.scrape_data(limit=10)

        assert len(result) == 0

        # Check error message
        captured = capsys.readouterr()
        assert 'failed to fetch' in captured.out

    def test_scrape_data_stops_on_no_entries(self, monkeypatch, capsys):
        """Test scraping stops when no entries found."""
        def mock_fetch(url):
            return '<html><body>No entries</body></html>'

        monkeypatch.setattr('scrape._fetch_url', mock_fetch)

        result = scrape.scrape_data(limit=10)

        assert len(result) == 0

        # Check message
        captured = capsys.readouterr()
        assert 'no entries found' in captured.out


@pytest.mark.integration
class TestSaveData:
    """Test data saving function."""

    def test_save_data_to_json(self, tmp_path, capsys):
        """Test saving scraped data to JSON file."""
        output_file = tmp_path / "test_output.json"
        test_data = [
            {'university': 'Stanford', 'program': 'CS'},
            {'university': 'MIT', 'program': 'EE'}
        ]

        scrape.save_data(test_data, str(output_file))

        # Verify file exists and contains correct data
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        assert len(loaded) == 2
        assert loaded[0]['university'] == 'Stanford'

        # Check console output
        captured = capsys.readouterr()
        assert 'wrote' in captured.out
        assert '2 entries' in captured.out


@pytest.mark.integration
class TestScrapeRowWithFewCells:
    """Test scrape.py handling of rows with fewer than 4 cells."""

    def test_extract_entries_skips_short_rows(self, monkeypatch):
        """Test that rows with < 4 cells are skipped."""
        html_content = '''
        <html><body>
        <table>
            <tr><th>Header</th></tr>
            <tr>
                <td>Only</td>
                <td>Two</td>
            </tr>
            <tr>
                <td>Stanford University</td>
                <td><span>Computer Science</span><span>PhD</span></td>
                <td>01 Feb 2026</td>
                <td>Accepted on 28 Jan</td>
                <td><a href="/result/123">View</a></td>
            </tr>
        </table>
        </body></html>
        '''

        monkeypatch.setattr('scrape._extract_comments_from_result_page', lambda url: None)

        result = scrape._extract_entries_from_page(html_content, 'https://test.com')

        # Should only extract the valid row, not the short one
        assert len(result) == 1
        assert result[0]['university'] == 'Stanford University'


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
