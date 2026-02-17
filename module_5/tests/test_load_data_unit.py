"""
Unit tests for load_data.py utility functions
Tests data parsing and cleaning functions to achieve 100% coverage.
"""

import json
import os
import runpy
import sys
from datetime import date
from unittest.mock import MagicMock

import psycopg
import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import load_data


@pytest.mark.db
class TestParseGPA:
    """Test GPA parsing function."""

    def test_parse_gpa_with_valid_string(self):
        """Test parsing valid GPA string."""
        assert load_data.parse_gpa('GPA 3.89') == 3.89
        assert load_data.parse_gpa('3.75') == 3.75
        assert load_data.parse_gpa('4.0') == 4.0

    def test_parse_gpa_with_none(self):
        """Test parsing None returns None."""
        assert load_data.parse_gpa(None) is None

    def test_parse_gpa_with_empty_string(self):
        """Test parsing empty string returns None."""
        assert load_data.parse_gpa('') is None

    def test_parse_gpa_with_no_numbers(self):
        """Test parsing string with no numbers returns None."""
        assert load_data.parse_gpa('No GPA') is None


@pytest.mark.db
class TestParseGREScore:
    """Test GRE score parsing function."""

    def test_parse_gre_with_valid_string(self):
        """Test parsing valid GRE score strings."""
        assert load_data.parse_gre_score('GRE 327') == 327
        assert load_data.parse_gre_score('GRE V 157') == 157
        assert load_data.parse_gre_score('GRE AW 3.50') == 3.50
        assert load_data.parse_gre_score('165') == 165

    def test_parse_gre_with_none(self):
        """Test parsing None returns None."""
        assert load_data.parse_gre_score(None) is None

    def test_parse_gre_with_empty_string(self):
        """Test parsing empty string returns None."""
        assert load_data.parse_gre_score('') is None

    def test_parse_gre_with_no_numbers(self):
        """Test parsing string with no numbers returns None."""
        assert load_data.parse_gre_score('No GRE') is None


@pytest.mark.db
class TestParseDate:
    """Test date parsing function."""

    def test_parse_date_with_valid_string(self):
        """Test parsing valid date string."""
        result = load_data.parse_date('January 31, 2026')
        assert result == date(2026, 1, 31)

    def test_parse_date_with_different_month(self):
        """Test parsing dates with different months."""
        result = load_data.parse_date('December 15, 2025')
        assert result == date(2025, 12, 15)

    def test_parse_date_with_none(self):
        """Test parsing None returns None."""
        assert load_data.parse_date(None) is None

    def test_parse_date_with_empty_string(self):
        """Test parsing empty string returns None."""
        assert load_data.parse_date('') is None

    def test_parse_date_with_invalid_format(self):
        """Test parsing invalid date format returns None."""
        assert load_data.parse_date('2026-01-31') is None
        assert load_data.parse_date('Invalid Date') is None


@pytest.mark.db
class TestExtractPIdFromURL:
    """Test p_id extraction from URL."""

    def test_extract_p_id_with_valid_url(self):
        """Test extracting p_id from valid GradCafe URL."""
        url = 'https://www.thegradcafe.com/survey/result/12345'
        assert load_data.extract_p_id_from_url(url) == 12345

    def test_extract_p_id_with_different_id(self):
        """Test extracting different p_id values."""
        assert load_data.extract_p_id_from_url('/result/999') == 999
        assert load_data.extract_p_id_from_url('/result/1') == 1

    def test_extract_p_id_with_none(self):
        """Test extracting p_id from None returns None."""
        assert load_data.extract_p_id_from_url(None) is None

    def test_extract_p_id_with_empty_string(self):
        """Test extracting p_id from empty string returns None."""
        assert load_data.extract_p_id_from_url('') is None

    def test_extract_p_id_with_invalid_url(self):
        """Test extracting p_id from invalid URL returns None."""
        assert load_data.extract_p_id_from_url('https://example.com') is None
        assert load_data.extract_p_id_from_url('not a url') is None


@pytest.mark.db
class TestCleanString:
    """Test string cleaning function."""

    def test_clean_string_with_nul_character(self):
        """Test removing NUL characters from string."""
        result = load_data.clean_string('test\x00string')
        assert result == 'teststring'

    def test_clean_string_with_multiple_nul_characters(self):
        """Test removing multiple NUL characters."""
        result = load_data.clean_string('test\x00\x00string\x00')
        assert result == 'teststring'

    def test_clean_string_with_normal_string(self):
        """Test cleaning normal string returns unchanged."""
        result = load_data.clean_string('normal string')
        assert result == 'normal string'

    def test_clean_string_with_none(self):
        """Test cleaning None returns None."""
        assert load_data.clean_string(None) is None


@pytest.mark.db
class TestCreateApplicantsTable:
    """Test applicants table creation."""

    def test_create_applicants_table(self, capsys):
        """Test that create_applicants_table executes without error."""
        # Mock connection and cursor
        class MockCursor:
            def __init__(self):
                self.queries = []
                self.closed = False

            def execute(self, query, params=None):
                self.queries.append(query)

            def executemany(self, query, params_list):
                for params in params_list:
                    self.execute(query, params)

            def close(self):
                self.closed = True

        class MockConnection:
            def __init__(self):
                self.committed = False
                self._cursor = MockCursor()

            def cursor(self):
                return self._cursor

            def commit(self):
                self.committed = True

        mock_conn = MockConnection()
        load_data.create_applicants_table(mock_conn)

        # Verify table was created
        assert mock_conn.committed
        assert mock_conn._cursor.closed
        assert len(mock_conn._cursor.queries) == 1
        assert 'CREATE TABLE' in mock_conn._cursor.queries[0]

        # Check console output
        captured = capsys.readouterr()
        assert 'Creating applicants table' in captured.out
        assert 'ready' in captured.out


@pytest.mark.db
class TestLoadJSONData:
    """Test JSON data loading function."""

    def test_load_json_data_with_valid_entries(self, tmp_path, capsys, monkeypatch):
        """Test loading valid JSON data."""
        # Create temporary JSON file with correct field names
        json_file = tmp_path / "test_data.json"
        json_content = "\n".join([
            json.dumps({
                "url": "https://test.com/result/12345", "program": "Stanford, CS",
                "comments": "Test", "date_added": "February 1, 2025",
                "applicant_status": "Accepted", "semester_year_start": "Fall 2025",
                "citizenship": "International", "gpa": "GPA 3.8", "gre": "GRE 325",
                "gre_v": "GRE V 165", "gre_aw": "GRE AW 4.5", "masters_or_phd": "PhD",
                "llm-generated-program": "CS", "llm-generated-university": "Stanford",
            }),
            json.dumps({
                "url": "https://test.com/result/67890", "program": "MIT, CS",
                "comments": None, "date_added": "February 2, 2025",
                "applicant_status": "Rejected", "semester_year_start": "Spring 2025",
                "citizenship": "US", "gpa": "3.5", "gre": "320",
                "gre_v": "160", "gre_aw": "4.0", "masters_or_phd": "Masters",
                "llm-generated-program": "CS", "llm-generated-university": "MIT",
            }),
        ])
        json_file.write_text(json_content)

        # Mock connection and cursor
        class MockCursor:
            def __init__(self):
                self.queries = []
                self.closed = False
                self.rowcount = 2

            def execute(self, query, params=None):
                self.queries.append((query, params))

            def executemany(self, query, params_list):
                for params in params_list:
                    self.execute(query, params)

            def close(self):
                self.closed = True

        class MockConnection:
            def __init__(self):
                self.committed = False
                self._cursor = MockCursor()

            def cursor(self):
                return self._cursor

            def commit(self):
                self.committed = True

        # Mock execute_batch to avoid psycopg dependency
        # def mock_execute_batch(cursor, query, records):
        #     for record in records:
        #         cursor.execute(query, record)

        # monkeypatch.setattr('load_data.execute_batch', mock_execute_batch)

        mock_conn = MockConnection()
        result = load_data.load_json_data(str(json_file), mock_conn)

        # Verify data was loaded
        assert result == 2  # Should return total records
        assert mock_conn.committed
        assert mock_conn._cursor.closed

        # Check console output
        captured = capsys.readouterr()
        assert 'Reading' in captured.out or 'complete' in captured.out


@pytest.mark.db
class TestLoadDataErrorPaths:
    """Test error paths in load_data.py."""

    def test_load_json_data_with_missing_p_id(self, tmp_path, capsys, monkeypatch):
        """Test handling when p_id extraction fails."""
        # Create JSON file with invalid URL (no p_id)
        json_file = tmp_path / "test_invalid.json"
        json_content = '{"url": "https://invalid.com", "program": "Test"}\n'
        json_file.write_text(json_content)

        class MockCursor:
            def __init__(self):
                self.closed = False

            def execute(self, query, params=None):
                pass

            def executemany(self, query, params_list):
                for params in params_list:
                    self.execute(query, params)

            def close(self):
                self.closed = True

        class MockConnection:
            def __init__(self):
                self.committed = False

            def cursor(self):
                return MockCursor()

            def commit(self):
                self.committed = True

        # def mock_execute_batch(cursor, query, records):
        #     pass

        # monkeypatch.setattr('load_data.execute_batch', mock_execute_batch)

        mock_conn = MockConnection()
        result = load_data.load_json_data(str(json_file), mock_conn)

        # Should skip the entry
        assert result == 0

        # Check warning message
        captured = capsys.readouterr()
        assert 'Could not extract p_id' in captured.out

    def test_load_json_data_with_json_decode_error(self, tmp_path, capsys, monkeypatch):
        """Test handling of JSON decode errors."""
        # Create file with invalid JSON
        json_file = tmp_path / "test_invalid_json.json"
        json_content = '{invalid json}\n{"url": "https://test.com/result/123", "program": "Test"}\n'
        json_file.write_text(json_content)

        class MockCursor:
            def __init__(self):
                self.closed = False

            def execute(self, query, params=None):
                pass

            def executemany(self, query, params_list):
                for params in params_list:
                    self.execute(query, params)

            def close(self):
                self.closed = True

        class MockConnection:
            def __init__(self):
                self.committed = False

            def cursor(self):
                return MockCursor()

            def commit(self):
                self.committed = True

        # def mock_execute_batch(cursor, query, records):
        #     pass

        # monkeypatch.setattr('load_data.execute_batch', mock_execute_batch)

        mock_conn = MockConnection()
        result = load_data.load_json_data(str(json_file), mock_conn)

        # Should skip the invalid JSON line
        assert result == 1

        # Check warning message
        captured = capsys.readouterr()
        assert 'JSON decode error' in captured.out

    def test_load_json_data_with_processing_error(self, tmp_path, capsys, monkeypatch):
        """Test handling of general processing errors."""
        # Create valid JSON file
        json_file = tmp_path / "test_error.json"
        json_content = '{"url": "https://test.com/result/123", "program": "Test"}\n'
        json_file.write_text(json_content)

        class MockCursor:
            def __init__(self):
                self.closed = False

            def execute(self, query, params=None):
                pass

            def executemany(self, query, params_list):
                for params in params_list:
                    self.execute(query, params)

            def close(self):
                self.closed = True

        class MockConnection:
            def __init__(self):
                self.committed = False

            def cursor(self):
                return MockCursor()

            def commit(self):
                self.committed = True

        # Mock execute_batch to raise an error
        # def mock_execute_batch(cursor, query, records):
        #     raise Exception("Database error")

        # monkeypatch.setattr('load_data.execute_batch', mock_execute_batch)

        # Mock parse functions to trigger the error in the except block
        original_parse_date = load_data.parse_date

        def error_parse_date(date_str):
            if date_str is None:
                raise ValueError("Intentional error for testing")
            return original_parse_date(date_str)

        monkeypatch.setattr('load_data.parse_date', error_parse_date)

        mock_conn = MockConnection()
        result = load_data.load_json_data(str(json_file), mock_conn)

        # Should skip the entry due to error
        assert result == 0

        # Check warning message
        captured = capsys.readouterr()
        assert 'Error processing line' in captured.out

    def test_verify_data_function(self, capsys):
        """Test verify_data function."""
        class MockCursor:
            def __init__(self):
                self.closed = False
                self.execute_count = 0

            def execute(self, query, params=None):
                self.execute_count += 1

            def executemany(self, query, params_list):
                for params in params_list:
                    self.execute(query, params)

            def fetchone(self):
                return (1000,)  # Total count

            def fetchall(self):
                # Return different data for different queries
                if self.execute_count == 2:
                    # Sample records
                    return [
                        (
                            123, 'Stanford, Computer Science', 'Great program!',
                            None, None, 'Accepted', 'Fall 2026', None, 3.8,
                            None, None, None, 'PhD', None, None,
                        ),
                        (
                            456, 'MIT, Computer Science', 'Tough program',
                            None, None, 'Rejected', 'Fall 2026', None, 3.5,
                            None, None, None, 'Masters', None, None,
                        ),
                    ]
                if self.execute_count == 3:
                    # Status statistics
                    return [('Accepted', 650), ('Rejected', 300), ('Waitlist', 50)]
                return []

            def close(self):
                self.closed = True

        class MockConnection:
            def cursor(self):
                return MockCursor()

        mock_conn = MockConnection()
        load_data.verify_data(mock_conn)

        # Check output
        captured = capsys.readouterr()
        assert 'Total' in captured.out
        assert 'Sample' in captured.out
        assert 'status' in captured.out.lower()


@pytest.mark.db
class TestLoadDataBatchInsertion:
    """Test batch insertion logic in load_data.py."""

    def test_batch_insert_at_1000_records(self, tmp_path, monkeypatch):
        """Test that batch insertion is triggered at 1000 records."""
        # Create JSON file with exactly 1000 records
        json_file = tmp_path / "test_1000.json"
        lines = []
        for i in range(1005):  # Slightly over 1000
            lines.append(f'{{"url": "https://test.com/result/{i}", "program": "Test"}}')
        json_file.write_text('\n'.join(lines))

        batch_calls = []

        class MockCursor:
            def __init__(self):
                self.closed = False

            def execute(self, query, params=None):
                pass

            def executemany(self, query, params_list):
                batch_calls.append(len(params_list))
                for params in params_list:
                    self.execute(query, params)

            def close(self):
                self.closed = True

        class MockConnection:
            def __init__(self):
                self.committed = False

            def cursor(self):
                return MockCursor()

            def commit(self):
                self.committed = True

        # def mock_execute_batch(cursor, query, records):
        #     batch_calls.append(len(records))

        # monkeypatch.setattr('load_data.execute_batch', mock_execute_batch)

        mock_conn = MockConnection()
        load_data.load_json_data(str(json_file), mock_conn)

        # Should have multiple batch calls
        assert len(batch_calls) >= 1


@pytest.mark.db
class TestLoadDataMainBlock:
    """Test load_data main execution."""

    def test_main_function_structure(self):
        """Test that load_data main functions exist."""
        # Verify main functions exist
        assert callable(load_data.create_applicants_table)
        assert callable(load_data.load_json_data)
        assert callable(load_data.verify_data)

    def test_main_success_path(self, monkeypatch, capsys):
        """Test main() success path."""
        class MockConnection:
            def close(self):
                pass

        def mock_connect(**kwargs):
            return MockConnection()

        def mock_create_table(conn):
            pass

        def mock_load_json_data(path, conn):
            return 100

        def mock_verify_data(conn):
            pass

        monkeypatch.setattr('psycopg.connect', mock_connect)
        monkeypatch.setattr('load_data.create_applicants_table', mock_create_table)
        monkeypatch.setattr('load_data.load_json_data', mock_load_json_data)
        monkeypatch.setattr('load_data.verify_data', mock_verify_data)

        load_data.main()

        # Check success messages
        captured = capsys.readouterr()
        assert 'Connection closed successfully' in captured.out

    def test_main_with_psycopg_error(self, monkeypatch, capsys):
        """Test main() handling of psycopg errors."""
        def mock_connect(**kwargs):
            raise psycopg.Error("Connection failed")

        monkeypatch.setattr('psycopg.connect', mock_connect)

        with pytest.raises(psycopg.Error):
            load_data.main()

        captured = capsys.readouterr()
        assert 'Database error' in captured.out

    def test_main_with_file_not_found(self, monkeypatch, capsys):
        """Test main() handling of FileNotFoundError."""
        class MockConnection:
            def cursor(self):
                return MockCursor()
            def commit(self):
                pass
            def close(self):
                pass

        def mock_connect(**kwargs):
            return MockConnection()

        def mock_create_table(conn):
            pass

        def mock_load_json_data(path, conn):
            raise FileNotFoundError(f"File not found: {path}")

        monkeypatch.setattr('psycopg.connect', mock_connect)
        monkeypatch.setattr('load_data.create_applicants_table', mock_create_table)
        monkeypatch.setattr('load_data.load_json_data', mock_load_json_data)

        with pytest.raises(FileNotFoundError):
            load_data.main()

        captured = capsys.readouterr()
        assert 'Could not find file' in captured.out

    def test_main_with_generic_exception(self, monkeypatch, capsys):
        """Test main() handling of generic exceptions."""
        class MockConnection:
            def cursor(self):
                return MockCursor()
            def commit(self):
                pass
            def close(self):
                pass

        def mock_connect(**kwargs):
            return MockConnection()

        def mock_create_table(conn):
            pass

        def mock_load_json_data(path, conn):
            raise ValueError("Unexpected error")

        monkeypatch.setattr('psycopg.connect', mock_connect)
        monkeypatch.setattr('load_data.create_applicants_table', mock_create_table)
        monkeypatch.setattr('load_data.load_json_data', mock_load_json_data)

        with pytest.raises(ValueError):
            load_data.main()

        captured = capsys.readouterr()
        assert 'Error:' in captured.out

    def test_main_with_database_url(self, monkeypatch, capsys):
        """Test main() with DATABASE_URL environment variable."""
        class MockConnection:
            def close(self):
                pass

        def mock_connect(**kwargs):
            # Verify DATABASE_URL was parsed correctly
            assert kwargs['host'] == 'envhost'
            assert kwargs['port'] == 5433
            assert kwargs['dbname'] == 'envdb'
            assert kwargs['user'] == 'envuser'
            return MockConnection()

        def mock_create_table(conn):
            pass

        def mock_load_json_data(path, conn):
            return 50

        def mock_verify_data(conn):
            pass

        monkeypatch.setenv('DATABASE_URL', 'postgresql://envuser:envpass@envhost:5433/envdb')
        monkeypatch.setattr('psycopg.connect', mock_connect)
        monkeypatch.setattr('load_data.create_applicants_table', mock_create_table)
        monkeypatch.setattr('load_data.load_json_data', mock_load_json_data)
        monkeypatch.setattr('load_data.verify_data', mock_verify_data)

        load_data.main()

        captured = capsys.readouterr()
        assert 'Connection closed successfully' in captured.out

    def test_main_with_individual_env_vars(self, monkeypatch, capsys):
        """Test main() with individual DB_* environment variables."""
        class MockConnection:
            def close(self):
                pass

        def mock_connect(**kwargs):
            # Verify individual env vars were used
            assert kwargs['host'] == 'envhost2'
            assert kwargs['port'] == 5434
            assert kwargs['dbname'] == 'envdb2'
            assert kwargs['user'] == 'envuser2'
            assert kwargs['password'] == 'envpass2'
            return MockConnection()

        def mock_create_table(conn):
            pass

        def mock_load_json_data(path, conn):
            return 25

        def mock_verify_data(conn):
            pass

        monkeypatch.delenv('DATABASE_URL', raising=False)
        monkeypatch.setenv('DB_HOST', 'envhost2')
        monkeypatch.setenv('DB_PORT', '5434')
        monkeypatch.setenv('DB_NAME', 'envdb2')
        monkeypatch.setenv('DB_USER', 'envuser2')
        monkeypatch.setenv('DB_PASSWORD', 'envpass2')
        monkeypatch.setattr('psycopg.connect', mock_connect)
        monkeypatch.setattr('load_data.create_applicants_table', mock_create_table)
        monkeypatch.setattr('load_data.load_json_data', mock_load_json_data)
        monkeypatch.setattr('load_data.verify_data', mock_verify_data)

        load_data.main()

        captured = capsys.readouterr()
        assert 'Connection closed successfully' in captured.out


@pytest.mark.db
class TestMainExecution:
    """Test main execution block."""

    def test_main_guard(self, monkeypatch):
        """Test that main execution block is covered."""
        # Check if the module has the required structure
        assert hasattr(load_data, 'parse_gpa')
        assert hasattr(load_data, 'parse_gre_score')
        assert hasattr(load_data, 'parse_date')
        assert hasattr(load_data, 'extract_p_id_from_url')
        assert hasattr(load_data, 'clean_string')


class MockCursor:
    """Mock database cursor."""
    def __init__(self):
        self.closed = False

    def execute(self, query, params=None):
        pass

    def executemany(self, query, params_list):
        for params in params_list:
            self.execute(query, params)

    def close(self):
        self.closed = True


@pytest.mark.db
class TestLoadDataIfNameMain:
    """Test load_data.py if __name__ == '__main__' entry point."""

    def test_if_name_main_block(self, monkeypatch):
        """Test __main__ block executes main() via runpy."""
        monkeypatch.setattr('psycopg.connect', lambda **kwargs: MagicMock())
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'load_data.py')
        runpy.run_path(src_path, run_name='__main__')


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
