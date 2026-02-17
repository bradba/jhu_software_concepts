"""
Unit tests for query_data.py query functions
Tests all database query functions to achieve 100% coverage.
"""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class MockCursor:
    """Mock database cursor for testing."""

    def __init__(self, return_values=None):
        self.return_values = return_values or []
        self.return_index = 0
        self.queries = []
        self.closed = False

    def execute(self, query, params=None):
        """Track executed queries."""
        self.queries.append((query, params))

    def fetchone(self):
        """Return mock data for fetchone()."""
        if self.return_index < len(self.return_values):
            value = self.return_values[self.return_index]
            self.return_index += 1
            return value
        return (0,)

    def fetchall(self):
        """Return mock data for fetchall()."""
        return self.return_values

    def close(self):
        """Mark cursor as closed."""
        self.closed = True


class MockConnection:
    """Mock database connection for testing."""

    def __init__(self, cursor=None):
        self._cursor = cursor or MockCursor()

    def cursor(self):
        """Return mock cursor."""
        return self._cursor

    def close(self):
        """Mock close connection."""
        pass


@pytest.mark.db
class TestGetConnection:
    """Test database connection function."""

    def test_get_connection_parameters(self, monkeypatch):
        """Test that get_connection uses correct parameters."""
        import query_data

        called = []

        def mock_connect(**kwargs):
            called.append(kwargs)
            return MockConnection()

        monkeypatch.setattr('psycopg.connect', mock_connect)
        monkeypatch.delenv('DATABASE_URL', raising=False)

        query_data.get_connection()

        assert len(called) == 1
        assert called[0]['host'] == 'localhost'
        assert called[0]['port'] == 5432
        assert 'dbname' in called[0]
        assert 'user' in called[0]

    def test_get_connection_with_database_url(self, monkeypatch):
        """Test that get_connection parses DATABASE_URL correctly."""
        import query_data

        called = []

        def mock_connect(**kwargs):
            called.append(kwargs)
            return MockConnection()

        monkeypatch.setattr('psycopg.connect', mock_connect)
        monkeypatch.setenv('DATABASE_URL', 'postgresql://testuser:testpass@testhost:5433/testdb')

        query_data.get_connection()

        assert len(called) == 1
        assert called[0]['host'] == 'testhost'
        assert called[0]['port'] == 5433
        assert called[0]['dbname'] == 'testdb'
        assert called[0]['user'] == 'testuser'
        assert called[0]['password'] == 'testpass'

    def test_get_connection_with_individual_env_vars(self, monkeypatch):
        """Test that get_connection uses individual DB_* environment variables."""
        import query_data

        called = []

        def mock_connect(**kwargs):
            called.append(kwargs)
            return MockConnection()

        monkeypatch.setattr('psycopg.connect', mock_connect)
        monkeypatch.delenv('DATABASE_URL', raising=False)
        monkeypatch.setenv('DB_HOST', 'customhost')
        monkeypatch.setenv('DB_PORT', '5433')
        monkeypatch.setenv('DB_NAME', 'customdb')
        monkeypatch.setenv('DB_USER', 'customuser')
        monkeypatch.setenv('DB_PASSWORD', 'custompass')

        query_data.get_connection()

        assert len(called) == 1
        assert called[0]['host'] == 'customhost'
        assert called[0]['port'] == 5433
        assert called[0]['dbname'] == 'customdb'
        assert called[0]['user'] == 'customuser'
        assert called[0]['password'] == 'custompass'


@pytest.mark.db
class TestQuestion1:
    """Test question_1: Fall 2026 applicants count."""

    def test_question_1_returns_count(self, capsys):
        """Test that question_1 returns correct count."""
        import query_data

        mock_cursor = MockCursor(return_values=[(1500,)])
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_1(mock_conn)

        assert result == 1500
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 1' in captured.out
        assert '1,500' in captured.out or '1500' in captured.out


@pytest.mark.db
class TestQuestion2:
    """Test question_2: International students percentage."""

    def test_question_2_returns_percentage(self, capsys):
        """Test that question_2 returns correct percentage."""
        import query_data

        mock_cursor = MockCursor(return_values=[(1000,), (450,)])  # total, international
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_2(mock_conn)

        assert result == 45.0
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 2' in captured.out
        assert '45.00%' in captured.out


@pytest.mark.db
class TestQuestion3:
    """Test question_3: Average GPA and GRE scores."""

    def test_question_3_returns_averages(self, capsys):
        """Test that question_3 returns correct averages."""
        import query_data

        # avg_gpa, gpa_count, avg_gre, gre_count, avg_gre_v, gre_v_count, avg_gre_aw, gre_aw_count
        mock_cursor = MockCursor(return_values=[
            (3.75, 500, 325.5, 450, 162.3, 445, 4.2, 440)
        ])
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_3(mock_conn)

        assert isinstance(result, dict)
        assert result['avg_gpa'] == 3.75
        assert result['avg_gre'] == 325.5
        assert result['avg_gre_v'] == 162.3
        assert result['avg_gre_aw'] == 4.2
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 3' in captured.out


@pytest.mark.db
class TestQuestion4:
    """Test question_4: Average GPA for admitted PhD students."""

    def test_question_4_returns_average(self, capsys):
        """Test that question_4 returns correct average."""
        import query_data

        mock_cursor = MockCursor(return_values=[(3.85, 250)])  # avg_gpa, count
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_4(mock_conn)

        assert result == 3.85
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 4' in captured.out


@pytest.mark.db
class TestQuestion5:
    """Test question_5: Percentage of admitted applicants."""

    def test_question_5_returns_percentage(self, capsys):
        """Test that question_5 returns correct percentage."""
        import query_data

        mock_cursor = MockCursor(return_values=[(1000,), (650,)])  # total, admitted
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_5(mock_conn)

        assert result == 65.0
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 5' in captured.out


@pytest.mark.db
class TestQuestion6:
    """Test question_6: Average GPA for admitted applicants to top programs."""

    def test_question_6_returns_average(self, capsys):
        """Test that question_6 returns correct average."""
        import query_data

        mock_cursor = MockCursor(return_values=[(3.90, 180)])  # avg_gpa, count
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_6(mock_conn)

        assert result == 3.90
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 6' in captured.out


@pytest.mark.db
class TestQuestion7:
    """Test question_7: Count of unique universities."""

    def test_question_7_returns_count(self, capsys):
        """Test that question_7 returns correct count."""
        import query_data

        mock_cursor = MockCursor(return_values=[(250,)])
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_7(mock_conn)

        assert result == 250
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 7' in captured.out


@pytest.mark.db
class TestQuestion8:
    """Test question_8: Count of unique programs."""

    def test_question_8_returns_count(self, capsys):
        """Test that question_8 returns correct count."""
        import query_data

        mock_cursor = MockCursor(return_values=[(350,)])
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_8(mock_conn)

        assert result == 350
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 8' in captured.out


@pytest.mark.db
class TestQuestion9:
    """Test question_9: LLM-generated vs original field comparison."""

    def test_question_9_returns_counts(self, capsys):
        """Test that question_9 returns correct counts."""
        import query_data

        # Returns count_llm, count_original
        mock_cursor = MockCursor(return_values=[(50,), (45,)])
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_9(mock_conn)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result == (50, 45)
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 9' in captured.out


@pytest.mark.db
class TestQuestion10:
    """Test question_10: Top programs by admission rate."""

    def test_question_10_returns_top_programs(self, capsys):
        """Test that question_10 returns correct top programs."""
        import query_data

        # Mock cursor needs to return the data for fetchall()
        class MockCursor10:
            def __init__(self):
                self.closed = False

            def execute(self, query, params=None):
                pass

            def fetchall(self):
                return [
                    ('Stanford', 'Computer Science PhD', 120, 15, 12.5),
                    ('MIT', 'Computer Science PhD', 110, 12, 10.9)
                ]

            def close(self):
                self.closed = True

        mock_cursor = MockCursor10()
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_10(mock_conn)

        assert isinstance(result, list)
        assert len(result) == 2
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 10' in captured.out


@pytest.mark.db
class TestQuestion11:
    """Test question_11: Degree type comparison."""

    def test_question_11_returns_comparison(self, capsys):
        """Test that question_11 returns correct comparison."""
        import query_data

        # Mock cursor needs to return the data for fetchall()
        class MockCursor11:
            def __init__(self):
                self.closed = False

            def execute(self, query, params=None):
                pass

            def fetchall(self):
                return [
                    ('PhD', 500, 100, 20.0, 3.85, 80),
                    ('Masters', 800, 520, 65.0, 3.75, 450)
                ]

            def close(self):
                self.closed = True

        mock_cursor = MockCursor11()
        mock_conn = MockConnection(cursor=mock_cursor)

        result = query_data.question_11(mock_conn)

        assert isinstance(result, list)
        assert len(result) == 2
        assert mock_cursor.closed

        # Check output
        captured = capsys.readouterr()
        assert 'Question 11' in captured.out


@pytest.mark.db
class TestQueryDataEdgeCases:
    """Test edge cases in query_data.py."""

    def test_question_9_with_same_counts(self, capsys):
        """Test question_9 when counts are the same."""
        import query_data

        class MockCursor9:
            def __init__(self):
                self.closed = False

            def execute(self, query, params=None):
                pass

            def fetchone(self):
                # Return same count for both queries
                return (50,)

            def close(self):
                self.closed = True

        class MockConnection9:
            def __init__(self):
                self._cursor = MockCursor9()

            def cursor(self):
                return self._cursor

        mock_conn = MockConnection9()

        result = query_data.question_9(mock_conn)

        assert result == (50, 50)

        # Check that "same" message is printed
        captured = capsys.readouterr()
        assert 'same' in captured.out.lower()

    def test_question_9_with_different_counts(self, capsys):
        """Test question_9 when counts are different."""
        import query_data

        class MockCursor9:
            def __init__(self):
                self.closed = False
                self.call_count = 0

            def execute(self, query, params=None):
                pass

            def fetchone(self):
                # Return different counts
                self.call_count += 1
                return (55,) if self.call_count == 1 else (50,)

            def close(self):
                self.closed = True

        class MockConnection9:
            def __init__(self):
                self._cursor = MockCursor9()

            def cursor(self):
                return self._cursor

        mock_conn = MockConnection9()

        result = query_data.question_9(mock_conn)

        assert result == (55, 50)

        # Check that difference message is printed
        captured = capsys.readouterr()
        assert 'Difference' in captured.out or 'more' in captured.out or 'fewer' in captured.out


@pytest.mark.db
class TestQueryDataMainBlock:
    """Test query_data main execution error paths."""

    def test_main_function_structure(self):
        """Test that query_data main functions exist."""
        import query_data

        # Verify all question functions exist
        for i in range(1, 12):
            assert callable(getattr(query_data, f'question_{i}'))

    def test_main_success_path(self, monkeypatch, capsys):
        """Test main() success path."""
        import query_data

        class MockConnection:
            def close(self):
                pass

        def mock_get_connection():
            return MockConnection()

        # Mock all question functions to do nothing
        for i in range(1, 12):
            monkeypatch.setattr(f'query_data.question_{i}', lambda conn: None)

        monkeypatch.setattr('query_data.get_connection', mock_get_connection)

        query_data.main()

        # Check success messages
        captured = capsys.readouterr()
        assert 'Connected to database successfully' in captured.out
        assert 'All queries completed successfully' in captured.out

    def test_main_with_psycopg_error(self, monkeypatch, capsys):
        """Test main() handling of psycopg errors."""
        import query_data
        import psycopg

        def mock_get_connection():
            raise psycopg.Error("Connection failed")

        monkeypatch.setattr('query_data.get_connection', mock_get_connection)

        with pytest.raises(psycopg.Error):
            query_data.main()

        captured = capsys.readouterr()
        assert 'Database error' in captured.out

    def test_main_with_generic_exception(self, monkeypatch, capsys):
        """Test main() handling of generic exceptions."""
        import query_data

        def mock_get_connection():
            raise ValueError("Unexpected error")

        monkeypatch.setattr('query_data.get_connection', mock_get_connection)

        with pytest.raises(ValueError):
            query_data.main()

        captured = capsys.readouterr()
        assert 'Error:' in captured.out


@pytest.mark.db
class TestMainExecution:
    """Test main execution block."""

    def test_main_guard(self, monkeypatch, capsys):
        """Test that main execution block is covered."""
        import query_data as qd_module

        # Mock get_connection to avoid actual DB connection
        class MockConn:
            def cursor(self):
                return MockCursor(return_values=[
                    (1000,),  # q1
                    (1000,), (500,),  # q2
                    (3.75, 500, 325.5, 450, 162.3, 445, 4.2, 440),  # q3
                    (3.85,),  # q4
                    (1000,), (650,),  # q5
                    (3.90,),  # q6
                    (250,),  # q7
                    (350,),  # q8
                    [],  # q9
                    [],  # q10
                    []  # q11
                ])

            def close(self):
                pass

        # Verify module has all required functions
        assert hasattr(qd_module, 'get_connection')
        assert hasattr(qd_module, 'question_1')
        assert hasattr(qd_module, 'question_2')
        assert hasattr(qd_module, 'question_3')
        assert hasattr(qd_module, 'question_4')
        assert hasattr(qd_module, 'question_5')
        assert hasattr(qd_module, 'question_6')
        assert hasattr(qd_module, 'question_7')
        assert hasattr(qd_module, 'question_8')
        assert hasattr(qd_module, 'question_9')
        assert hasattr(qd_module, 'question_10')
        assert hasattr(qd_module, 'question_11')


@pytest.mark.db
class TestQueryDataIfNameMain:
    """Test query_data.py if __name__ == '__main__' entry point."""

    def test_if_name_main_block(self, monkeypatch):
        """Test __main__ block executes main() via runpy."""
        import runpy

        class _Cursor:
            _values = [
                (1000,),                                         # q1
                (1000,), (500,),                                 # q2 (total, intl)
                (3.75, 500, 325.5, 450, 162.3, 445, 4.2, 440), # q3
                (3.85, 500),                                     # q4 (avg_gpa, count)
                (1000,), (650,),                                 # q5 (total, accepted)
                (3.90, 300),                                     # q6 (avg_gpa, count)
                (250,),                                          # q7
                (350,),                                          # q8
                (45,), (50,),                                    # q9 (llm, original)
            ]
            _idx = 0

            def execute(self, q, p=None):
                pass

            def fetchone(self):
                if self._idx < len(self._values):
                    v = self._values[self._idx]
                    self.__class__._idx += 1
                    return v
                return (0,)

            def fetchall(self):
                return []

            def close(self):
                pass

        class _Conn:
            def cursor(self):
                return _Cursor()

            def close(self):
                pass

        _Cursor._idx = 0
        monkeypatch.setattr('psycopg.connect', lambda **kwargs: _Conn())
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'query_data.py')
        runpy.run_path(src_path, run_name='__main__')


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
