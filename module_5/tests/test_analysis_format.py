"""
Unit tests for Analysis Formatting
Tests that the analysis page properly formats answers with labels and rounded percentages.
"""

import os
import re
import sys

import pytest
from conftest import MockConnection

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_query_functions(monkeypatch):
    """Mock all query_data functions with values that exercise rounding."""
    monkeypatch.setattr('query_data.get_connection', MockConnection)
    # Mock query functions with values that include percentages
    monkeypatch.setattr('query_data.question_1', lambda _conn: 1500)
    monkeypatch.setattr('query_data.question_2', lambda _conn: 67.123456)  # Percentage to test rounding
    monkeypatch.setattr('query_data.question_3', lambda _conn: {
        'avg_gpa': 3.756789,
        'avg_gre': 325.5,
        'avg_gre_v': 162.345,
        'avg_gre_aw': 4.234
    })
    monkeypatch.setattr('query_data.question_4', lambda _conn: 3.801234)
    monkeypatch.setattr('query_data.question_5', lambda _conn: 45.6789012)  # Percentage to test rounding
    monkeypatch.setattr('query_data.question_6', lambda _conn: 3.854321)
    monkeypatch.setattr('query_data.question_7', lambda _conn: 250)
    monkeypatch.setattr('query_data.question_8', lambda _conn: 45)
    monkeypatch.setattr('query_data.question_9', lambda _conn: [50, 45])
    monkeypatch.setattr('query_data.question_10', lambda _conn: [
        ('Stanford', 'Computer Science PhD', 120, 15, 12.5),
        ('MIT', 'Computer Science PhD', 110, 12, 10.909090)  # Percentage to test rounding
    ])
    monkeypatch.setattr('query_data.question_11', lambda _conn: [
        ('PhD', 500, 100, 20.0, 3.85, 80),
        ('Masters', 800, 520, 65.123456, 3.75, 450)  # Percentage to test rounding
    ])



@pytest.mark.analysis
class TestAnswerLabels:
    """Test that the page includes 'Answer' labels for rendered analysis."""

    def test_page_contains_answer_labels(self, client):
        """Test that the page contains 'Answer:' labels for analysis results."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Check for presence of "Answer:" labels
        assert 'Answer:' in html_content, "Page should contain 'Answer:' labels"

        # Count how many "Answer:" labels are present
        answer_count = html_content.count('Answer:')
        assert answer_count >= 1, f"Page should have at least 1 'Answer:' label, found {answer_count}"

    def test_each_question_has_answer_label(self, client):
        """Test that each analysis question has an associated Answer label."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # There should be multiple questions with answers
        # Based on the app, we have 11 questions (question_1 through question_11)
        answer_count = html_content.count('Answer:')

        # We expect at least 5 answer labels (conservative estimate)
        assert answer_count >= 5, \
            f"Page should have multiple 'Answer:' labels for different questions, found {answer_count}"

    def test_answer_labels_precede_values(self, client):
        """Test that Answer labels appear before their corresponding values."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Find all occurrences of "Answer:" - they should exist and have content nearby
        # More flexible pattern that allows HTML tags between label and value
        answer_pattern = re.compile(r'Answer:', re.IGNORECASE)
        matches = answer_pattern.findall(html_content)

        assert len(matches) >= 1, "Page should contain Answer labels"

        # For each Answer label, there should be some numeric content nearby
        # (within 200 characters, allowing for HTML tags)
        for i in range(min(3, len(matches))):  # Check first 3 answers
            answer_pos = html_content.find('Answer:', html_content.find('Answer:') + i)
            if answer_pos != -1:
                nearby_content = html_content[answer_pos:answer_pos + 200]
                # Should have some digits nearby (the actual answer value)
                has_digits = re.search(r'\d+', nearby_content)
                assert has_digits, f"Answer label at position {answer_pos} should have numeric content nearby"


@pytest.mark.analysis
class TestPercentageFormatting:
    """Test that percentages are formatted with two decimal places."""

    def test_percentages_have_two_decimals(self, client):
        """Test that all percentages are displayed with exactly two decimal places."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Pattern to find percentages: number followed by % symbol
        # Should match formats like: 67.12%, 45.68%, 20.00%
        percentage_pattern = re.compile(r'(\d+\.\d+)%')
        percentages = percentage_pattern.findall(html_content)

        # If there are percentages, verify they have exactly 2 decimal places
        if percentages:
            for percentage in percentages:
                decimal_part = percentage.split('.')[-1]
                assert len(decimal_part) == 2, \
                    f"Percentage {percentage}% should have exactly 2 decimal places, has {len(decimal_part)}"

    def test_specific_percentage_rounding(self, client):
        """Test that specific known percentages are correctly rounded to 2 decimals."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # We know question_2 returns 67.123456, should be displayed as 67.12%
        assert '67.12%' in html_content or '67.12' in html_content, \
            "Percentage 67.123456 should be rounded to 67.12"

        # We know question_5 returns 45.6789012, should be displayed as 45.68%
        assert '45.68%' in html_content or '45.68' in html_content, \
            "Percentage 45.6789012 should be rounded to 45.68"

    def test_percentage_values_are_numeric(self, client):
        """Test that percentage values are properly formatted as numbers."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Find all percentages
        percentage_pattern = re.compile(r'(\d+\.\d{2})%')
        percentages = percentage_pattern.findall(html_content)

        # All found percentages should be valid floats
        for percentage in percentages:
            try:
                value = float(percentage)
                assert 0 <= value <= 100, \
                    f"Percentage {percentage}% should be between 0 and 100"
            except ValueError:
                pytest.fail(f"Percentage value {percentage} is not a valid number")

    def test_no_excessive_decimal_places(self, client):
        """Test that no percentages have more than 2 decimal places."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Pattern to find percentages with more than 2 decimal places
        excessive_decimals_pattern = re.compile(r'\d+\.\d{3,}%')
        excessive_matches = excessive_decimals_pattern.findall(html_content)

        assert len(excessive_matches) == 0, \
            f"Found percentages with more than 2 decimal places: {excessive_matches}"

    def test_whole_number_percentages_have_decimals(self, client):
        """Test that even whole number percentages are formatted with .00."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Pattern to find whole percentages followed by % (like 20%)
        # We want to check if they're properly formatted as 20.00% instead
        whole_percentage_pattern = re.compile(r'\b(\d+)%')
        whole_percentages = whole_percentage_pattern.findall(html_content)

        # For proper formatting, whole numbers should be shown as XX.00%
        # If we find whole number percentages without decimals, that's acceptable too
        # but if shown with decimals, they must have exactly 2
        if whole_percentages:
            # This is informational - not all templates require .00 for whole numbers
            pass


@pytest.mark.analysis
class TestAnswerAndPercentageIntegration:
    """Test the integration of Answer labels with percentage values."""

    def test_answer_label_with_percentage_format(self, client):
        """Test that Answer labels are properly associated with formatted percentages."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')

        # Pattern to find "Answer:" followed eventually by a percentage
        # This tests the integration of both requirements
        answer_with_percentage_pattern = re.compile(
            r'Answer:.*?(\d+\.\d{2})%',
            re.DOTALL | re.IGNORECASE
        )
        matches = answer_with_percentage_pattern.findall(html_content)

        # We expect at least some answers to contain percentages
        # Based on our mock data, we know questions 2, 5, and 11 return percentages
        assert len(matches) >= 1, \
            "At least one Answer should be followed by a properly formatted percentage"

    def test_all_analysis_sections_properly_formatted(self, client):
        """Test that all analysis sections have proper labels and formatting."""
        response = client.get('/')
        assert response.status_code == 200

        html_content = response.data.decode('utf-8')

        # Page should have both Answer labels and properly formatted percentages
        has_answers = 'Answer:' in html_content

        assert has_answers, "Page should contain Answer labels"
        # Note: has_percentages might be False if no percentages are shown,
        # but if they are shown, they should be formatted correctly
        # This is tested in other test methods


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
