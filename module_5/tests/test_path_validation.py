"""Tests for path validation in clean.py and scrape.py."""

import pytest
from unittest import mock
from clean import _validate_file_path as clean_validate
from scrape import _validate_file_path as scrape_validate


class TestPathValidationClean:
    """Test path validation in clean module."""

    def test_validate_file_path_normal(self):
        """_validate_file_path returns absolute path for normal input."""
        result = clean_validate("test.json", operation="test")
        assert result.endswith("test.json")
        assert result.startswith("/")

    def test_validate_file_path_rejects_null_bytes(self):
        """_validate_file_path raises ValueError for null bytes."""
        with pytest.raises(ValueError, match="null bytes"):
            clean_validate("test\0.json", operation="test")

    def test_validate_file_path_rejects_non_string(self):
        """_validate_file_path raises ValueError for non-string input."""
        with pytest.raises(ValueError, match="must be a string"):
            clean_validate(123, operation="test")

    def test_validate_file_path_warns_system_paths(self, capsys):
        """_validate_file_path warns when accessing system paths."""
        clean_validate("/etc/passwd", operation="test")
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "/etc/passwd" in captured.out

    def test_validate_file_path_handles_abspath_exception(self):
        """_validate_file_path handles exceptions from os.path.abspath."""
        with mock.patch('os.path.abspath', side_effect=ValueError("Invalid")):
            with pytest.raises(ValueError, match="Invalid path for test"):
                clean_validate("test.json", operation="test")


class TestPathValidationScrape:
    """Test path validation in scrape module."""

    def test_validate_file_path_normal(self):
        """_validate_file_path returns absolute path for normal input."""
        result = scrape_validate("output.json", operation="test")
        assert result.endswith("output.json")
        assert result.startswith("/")

    def test_validate_file_path_rejects_null_bytes(self):
        """_validate_file_path raises ValueError for null bytes."""
        with pytest.raises(ValueError, match="null bytes"):
            scrape_validate("output\0.json", operation="test")

    def test_validate_file_path_rejects_non_string(self):
        """_validate_file_path raises ValueError for non-string input."""
        with pytest.raises(ValueError, match="must be a string"):
            scrape_validate(None, operation="test")

    def test_validate_file_path_warns_system_paths(self, capsys):
        """_validate_file_path warns when accessing system paths."""
        scrape_validate("/sys/kernel", operation="test")
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "/sys/kernel" in captured.out

    def test_validate_file_path_handles_abspath_exception(self):
        """_validate_file_path handles exceptions from os.path.abspath."""
        with mock.patch('os.path.abspath', side_effect=TypeError("Invalid type")):
            with pytest.raises(ValueError, match="Invalid path for test"):
                scrape_validate("output.json", operation="test")
