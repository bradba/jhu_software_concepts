"""
Unit tests for clean.py utility functions
Tests data cleaning, HTML stripping, and LLM standardization functions.
"""

import importlib
import json
import os
import runpy
import sys
from unittest.mock import MagicMock

import pytest
import urllib3

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import clean


@pytest.mark.db
class TestStripHTML:
    """Test HTML stripping function."""

    def test_strip_html_with_tags(self):
        """Test removing HTML tags."""
        result = clean._strip_html('<p>Hello <b>World</b></p>')
        assert result == 'Hello World'

    def test_strip_html_with_entities(self):
        """Test removing HTML entities."""
        result = clean._strip_html('Test&nbsp;Text')
        assert 'Test' in result and 'Text' in result

    def test_strip_html_with_whitespace(self):
        """Test normalizing whitespace."""
        result = clean._strip_html('Test   Multiple    Spaces')
        assert result == 'Test Multiple Spaces'

    def test_strip_html_with_empty_string(self):
        """Test with empty string."""
        result = clean._strip_html('')
        assert result == ''

    def test_strip_html_with_none(self):
        """Test with None value."""
        result = clean._strip_html(None)
        assert result is None


@pytest.mark.db
class TestNormalizeValue:
    """Test value normalization function."""

    def test_normalize_none_value(self):
        """Test normalizing None."""
        result = clean._normalize_value(None, 'N/A')
        assert result == 'N/A'

    def test_normalize_empty_string(self):
        """Test normalizing empty string."""
        result = clean._normalize_value('', 'MISSING')
        assert result == 'MISSING'

    def test_normalize_html_string(self):
        """Test normalizing string with HTML."""
        result = clean._normalize_value('<p>Test</p>', None)
        assert result == 'Test'

    def test_normalize_non_string(self):
        """Test non-string values pass through."""
        result = clean._normalize_value(123, None)
        assert result == 123


@pytest.mark.db
class TestCleanRecord:
    """Test record cleaning function."""

    def test_clean_record_with_html(self):
        """Test cleaning record with HTML in values."""
        record = {
            'name': '<b>John</b>',
            'description': '<p>Test description</p>',
            'count': 5
        }
        result = clean._clean_record(record, None)

        assert result['name'] == 'John'
        assert result['description'] == 'Test description'
        assert result['count'] == 5

    def test_clean_record_with_missing_values(self):
        """Test cleaning record with None values."""
        record = {'name': None, 'value': ''}
        result = clean._clean_record(record, 'MISSING')

        assert result['name'] == 'MISSING'
        assert result['value'] == 'MISSING'


@pytest.mark.db
class TestCleanCommentText:
    """Test comment cleaning function."""

    def test_clean_comment_with_badges(self):
        """Test removing badge-like tokens."""
        text = 'This is a really great program with excellent faculty! Fall 2026 International GPA 3.8 GRE 325'
        result = clean._clean_comment_text(text)

        assert result == 'This is a really great program with excellent faculty!'

    def test_clean_comment_with_html(self):
        """Test cleaning HTML from comments."""
        text = '<p>This is a <b>great</b> program!</p> Fall 2026'
        result = clean._clean_comment_text(text)

        assert 'great' in result.lower()
        assert 'Fall 2026' not in result

    def test_clean_comment_with_acceptance_date(self):
        """Test removing acceptance/rejection dates."""
        text = 'Accepted on 15 Jan - very excited about this amazing opportunity! International'
        result = clean._clean_comment_text(text)

        assert 'excited' in result
        assert 'Accepted on' not in result

    def test_clean_comment_with_short_text(self):
        """Test that short text returns None."""
        result = clean._clean_comment_text('Short')
        assert result is None

    def test_clean_comment_with_only_punctuation(self):
        """Test that only punctuation returns None."""
        result = clean._clean_comment_text('... ,,, !!!')
        assert result is None

    def test_clean_comment_with_none(self):
        """Test with None."""
        result = clean._clean_comment_text(None)
        assert result is None

    def test_clean_comment_truncates_long_text(self):
        """Test that long comments are truncated to 500 chars."""
        long_text = 'A' * 600 + ' This is a great program!'
        result = clean._clean_comment_text(long_text)

        assert result is not None
        assert len(result) <= 500


@pytest.mark.db
class TestLoadData:
    """Test data loading function."""

    def test_load_data_from_json_file(self, tmp_path):
        """Test loading data from JSON file."""
        json_file = tmp_path / "test.json"
        test_data = [{'name': 'Test1'}, {'name': 'Test2'}]
        json_file.write_text(json.dumps(test_data))

        result = clean.load_data(str(json_file))

        assert len(result) == 2
        assert result[0]['name'] == 'Test1'

    def test_load_data_with_invalid_format(self, tmp_path):
        """Test that non-list JSON raises ValueError."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"not": "a list"}')

        with pytest.raises(ValueError, match="Expected a list"):
            clean.load_data(str(json_file))


@pytest.mark.db
class TestCleanData:
    """Test bulk data cleaning function."""

    def test_clean_data_multiple_records(self):
        """Test cleaning multiple records."""
        data = [
            {'name': '<b>Test1</b>', 'value': None},
            {'name': '<p>Test2</p>', 'value': ''}
        ]

        result = clean.clean_data(data, 'MISSING')

        assert len(result) == 2
        assert result[0]['name'] == 'Test1'
        assert result[0]['value'] == 'MISSING'
        assert result[1]['name'] == 'Test2'


@pytest.mark.db
class TestSaveData:
    """Test data saving function."""

    def test_save_data_to_json_file(self, tmp_path):
        """Test saving data to JSON file."""
        output_file = tmp_path / "output.json"
        test_data = [{'name': 'Test1'}, {'name': 'Test2'}]

        clean.save_data(test_data, str(output_file))

        # Verify file was created and contains correct data
        assert output_file.exists()
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert len(loaded) == 2
        assert loaded[0]['name'] == 'Test1'


@pytest.mark.db
class TestStandardizeUniversityWithLLM:
    """Test LLM standardization function."""

    def test_standardize_with_successful_api_call(self, monkeypatch):
        """Test successful LLM API call."""
        entry = {'university': 'Stanford', 'program_name': 'CS'}

        class MockResponse:
            status = 200
            def __init__(self):
                self.data = json.dumps([{
                    'university': 'Stanford',
                    'program_name': 'CS',
                    'llm-generated-university': 'Stanford University',
                    'llm-generated-program': 'Computer Science'
                }]).encode('utf-8')

        class MockHTTP:
            def request(self, *args, **kwargs):
                return MockResponse()

        monkeypatch.setattr('clean._http', MockHTTP())

        result = clean._standardize_university_with_llm(entry)

        assert 'llm-generated-university' in result
        assert result['llm-generated-university'] == 'Stanford University'

    def test_standardize_with_custom_api_url(self, monkeypatch):
        """Test LLM API call with custom URL."""
        entry = {'university': 'MIT', 'program_name': 'EE'}

        called_urls = []

        class MockResponse:
            status = 200
            def __init__(self):
                self.data = json.dumps([{
                    'university': 'MIT',
                    'program_name': 'EE',
                    'llm-generated-university': 'MIT',
                    'llm-generated-program': 'Electrical Engineering'
                }]).encode('utf-8')

        class MockHTTP:
            def request(self, method, url, *args, **kwargs):
                called_urls.append(url)
                return MockResponse()

        monkeypatch.setattr('clean._http', MockHTTP())

        # Test with explicit API URL
        result = clean._standardize_university_with_llm(entry, api_url='http://custom:9000/api')

        assert called_urls[0] == 'http://custom:9000/api'
        assert 'llm-generated-university' in result

    def test_standardize_uses_env_var_for_api_url(self, monkeypatch):
        """Test that LLM API uses LLM_API_URL environment variable."""
        # Reload the module to pick up the new environment variable
        monkeypatch.setenv('LLM_API_URL', 'http://envapi:8080/standardize')
        importlib.reload(clean)

        entry = {'university': 'CMU', 'program_name': 'CS'}

        called_urls = []

        class MockResponse:
            status = 200
            def __init__(self):
                self.data = json.dumps([entry]).encode('utf-8')

        class MockHTTP:
            def request(self, method, url, *args, **kwargs):
                called_urls.append(url)
                return MockResponse()

        monkeypatch.setattr('clean._http', MockHTTP())

        # Call without explicit api_url - should use environment variable
        clean._standardize_university_with_llm(entry)

        assert called_urls[0] == 'http://envapi:8080/standardize'

        # Reload again with default
        monkeypatch.delenv('LLM_API_URL', raising=False)
        importlib.reload(clean)

    def test_standardize_with_api_error(self, monkeypatch, capsys):
        """Test handling of API errors."""
        entry = {'university': 'Stanford', 'program_name': 'CS'}

        class MockResponse:
            status = 500
            data = b''

        class MockHTTP:
            def request(self, *args, **kwargs):
                return MockResponse()

        monkeypatch.setattr('clean._http', MockHTTP())

        result = clean._standardize_university_with_llm(entry)

        # Should return original entry on error
        assert result == entry

        # Check error message was printed
        captured = capsys.readouterr()
        assert 'HTTP 500' in captured.out

    def test_standardize_with_exception(self, monkeypatch, capsys):
        """Test handling of exceptions."""
        entry = {'university': 'Stanford', 'program_name': 'CS'}

        class MockHTTP:
            def request(self, *args, **kwargs):
                raise ConnectionError("Network error")

        monkeypatch.setattr('clean._http', MockHTTP())

        result = clean._standardize_university_with_llm(entry)

        # Should return original entry on exception
        assert result == entry

        # Check error message was printed
        captured = capsys.readouterr()
        assert 'error' in captured.out.lower()


@pytest.mark.db
class TestStandardizeWithLLM:
    """Test bulk LLM standardization function."""

    def test_standardize_multiple_entries(self, monkeypatch, capsys):
        """Test standardizing multiple entries."""
        data = [
            {'university': 'Stanford', 'program_name': 'CS'},
            {'university': 'MIT', 'program_name': 'EE'}
        ]

        call_count = [0]

        def mock_standardize(entry, api_url):
            call_count[0] += 1
            entry['llm-generated-university'] = entry['university'] + ' University'
            return entry

        monkeypatch.setattr('clean._standardize_university_with_llm', mock_standardize)

        result = clean._standardize_with_llm(data)

        assert len(result) == 2
        assert call_count[0] == 2

        # Check progress messages
        captured = capsys.readouterr()
        assert 'completed' in captured.out

    def test_standardize_with_flush(self, tmp_path, monkeypatch, capsys):
        """Test flushing progress to file."""
        output_file = tmp_path / "progress.json"
        data = [{'university': f'Univ{i}', 'program_name': 'CS'} for i in range(150)]

        def mock_standardize(entry, api_url):
            entry['llm-generated-university'] = entry['university']
            return entry

        monkeypatch.setattr('clean._standardize_university_with_llm', mock_standardize)

        result = clean._standardize_with_llm(
            data,
            output_path=str(output_file),
            flush_every=100
        )

        assert len(result) == 150

        # Check that progress was flushed
        captured = capsys.readouterr()
        assert 'flushed progress' in captured.out


@pytest.mark.db
class TestCleanMainBlock:
    """Test clean.py __main__ entry point."""

    def test_main_basic(self, tmp_path, monkeypatch):
        """Test __main__ block without --standardize."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        input_file.write_text('[{"university": "Stanford", "description": null}]')
        monkeypatch.setattr(sys, 'argv', [
            'clean.py', '--input', str(input_file), '--output', str(output_file)
        ])
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'clean.py')
        runpy.run_path(src_path, run_name='__main__')
        assert output_file.exists()

    def test_main_standardize_no_existing(self, tmp_path, monkeypatch):
        """Test __main__ block with --standardize and no existing output file."""
        class MockPoolManager:
            def request(self, method, url, body=None, headers=None):
                entries = json.loads(body) if body else []
                for e in entries:
                    e['llm-generated-university'] = 'Mock University'
                    e['llm-generated-program'] = 'Mock Program'
                resp = MagicMock()
                resp.status = 200
                resp.data = json.dumps(entries).encode('utf-8')
                return resp

        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        input_file.write_text('[{"university": "Stanford", "program_name": "CS"}]')
        monkeypatch.setattr(urllib3, 'PoolManager', MockPoolManager)
        monkeypatch.setattr(sys, 'argv', [
            'clean.py', '--input', str(input_file), '--output', str(output_file),
            '--standardize'
        ])
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'clean.py')
        runpy.run_path(src_path, run_name='__main__')
        assert output_file.exists()

    def test_main_standardize_with_existing(self, tmp_path, monkeypatch):
        """Test __main__ block with --standardize and existing output with LLM entries."""
        class MockPoolManager:
            def request(self, method, url, body=None, headers=None):
                entries = json.loads(body) if body else []
                for e in entries:
                    e['llm-generated-university'] = 'Mock University'
                    e['llm-generated-program'] = 'Mock Program'
                resp = MagicMock()
                resp.status = 200
                resp.data = json.dumps(entries).encode('utf-8')
                return resp

        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        input_file.write_text(json.dumps([
            {"university": "Stanford", "program_name": "CS"},
            {"university": "MIT", "program_name": "EE"},
        ]))
        # Pre-create output with one LLM-processed entry
        output_file.write_text(json.dumps([
            {"university": "Stanford", "program_name": "CS",
             "llm-generated-university": "Stanford University",
             "llm-generated-program": "Computer Science"},
        ]))
        monkeypatch.setattr(urllib3, 'PoolManager', MockPoolManager)
        monkeypatch.setattr(sys, 'argv', [
            'clean.py', '--input', str(input_file), '--output', str(output_file),
            '--standardize'
        ])
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'clean.py')
        runpy.run_path(src_path, run_name='__main__')
        assert output_file.exists()


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
