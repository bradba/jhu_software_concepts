"""Database loading module for GradCafe applicant data.

This module provides utilities for loading, parsing, and inserting applicant data
into a PostgreSQL database. It handles data cleaning, type conversion, and
database schema creation.

The module supports both batch loading from JSON files and individual record insertion.
It automatically handles duplicate entries using PostgreSQL's ON CONFLICT clause.

Example:
    Load data from a JSON file::

        from load_data import create_applicants_table, load_json_data
        import psycopg

        conn = psycopg.connect(host='localhost', dbname='mydb')
        create_applicants_table(conn)
        load_json_data('applicant_data.json', conn)
        conn.close()

Attributes:
    None

See Also:
    - :mod:`query_data`: For querying the loaded data
    - :mod:`clean`: For data cleaning utilities
    - :mod:`scrape`: For web scraping applicant data
"""

import json
import os
import re
from datetime import datetime

import psycopg
from psycopg import sql

from db import get_connection

# Maximum rows returned by any SELECT that supports a caller-supplied limit.
_LIMIT_MAX = 100

# Column order shared by load_json_data and app.pull_data.
_APPLICANT_COLS = (
    "p_id", "program", "comments", "date_added", "url", "status", "term",
    "us_or_international", "gpa", "gre", "gre_v", "gre_aw", "degree",
    "llm_generated_program", "llm_generated_university",
)

# Composed INSERT statement: table/column identifiers are quoted by psycopg;
# values stay as %s placeholders so the driver handles escaping.
APPLICANT_INSERT = sql.SQL(
    "INSERT INTO {table} ({cols}) VALUES ({vals})"
    " ON CONFLICT ({pk}) DO NOTHING"
).format(
    table=sql.Identifier("applicants"),
    cols=sql.SQL(", ").join(map(sql.Identifier, _APPLICANT_COLS)),
    vals=sql.SQL(", ").join(sql.Placeholder() for _ in _APPLICANT_COLS),
    pk=sql.Identifier("p_id"),
)


def _parse_numeric_str(s):
    """Extract the first numeric value from a string.

    Args:
        s (str): Input string, e.g. ``'GPA 3.89'`` or ``'GRE 327'``.

    Returns:
        float: First numeric value found, or None if absent or input is falsy.
    """
    if not s:
        return None
    match = re.search(r'(\d+\.?\d*)', s)
    return float(match.group(1)) if match else None


def parse_gpa(gpa_str):
    """Extract numeric GPA value from string.

    Parses strings like 'GPA 3.89' or '3.89' and extracts the numeric value.

    Args:
        gpa_str (str): String containing GPA information

    Returns:
        float: Extracted GPA value, or None if parsing fails

    Example:
        >>> parse_gpa('GPA 3.89')
        3.89
        >>> parse_gpa('3.5')
        3.5
        >>> parse_gpa('invalid')
        None
    """
    return _parse_numeric_str(gpa_str)


def parse_gre_score(gre_str):
    """Extract numeric GRE score from various string formats.

    Supports parsing of different GRE score formats including total scores,
    verbal scores, and analytical writing scores.

    Args:
        gre_str (str): String containing GRE score information

    Returns:
        float: Extracted GRE score, or None if parsing fails

    Example:
        >>> parse_gre_score('GRE 327')
        327.0
        >>> parse_gre_score('GRE V 157')
        157.0
        >>> parse_gre_score('GRE AW 3.50')
        3.5
    """
    return _parse_numeric_str(gre_str)


def parse_date(date_str):
    """Parse date string into date object.

    Converts date strings in the format 'Month DD, YYYY' to Python date objects.

    Args:
        date_str (str): Date string in format 'January 31, 2026'

    Returns:
        datetime.date: Parsed date object, or None if parsing fails

    Example:
        >>> parse_date('January 31, 2026')
        datetime.date(2026, 1, 31)
        >>> parse_date('invalid')
        None
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%B %d, %Y').date()
    except ValueError:
        return None


def extract_p_id_from_url(url):
    """Extract the post ID from a GradCafe result URL.

    Parses GradCafe URLs to extract the unique post identifier (p_id).
    URLs typically follow the pattern: https://www.thegradcafe.com/survey/result/123456

    Args:
        url (str): GradCafe result URL

    Returns:
        int: Extracted post ID, or None if URL doesn't match expected format

    Example:
        >>> extract_p_id_from_url('https://www.thegradcafe.com/survey/result/123456')
        123456
    """
    if not url:
        return None
    match = re.search(r'/result/(\d+)', url)
    return int(match.group(1)) if match else None


def clean_string(s):
    """Remove problematic characters from strings for PostgreSQL compatibility.

    Removes NUL characters (0x00) which PostgreSQL doesn't accept in text fields.

    Args:
        s (str): String to clean

    Returns:
        str: Cleaned string with NUL characters removed, or None if input is None

    Note:
        PostgreSQL will reject any string containing NUL bytes, so this function
        must be called on all user-provided text before insertion.
    """
    if s is None:
        return None
    # Remove NUL characters (0x00) which PostgreSQL doesn't accept
    return s.replace('\x00', '')


def create_applicants_table(conn):
    """Create the applicants table in the database if it doesn't exist.

    Creates a table with the following schema:
        - p_id (INTEGER PRIMARY KEY): Unique post identifier
        - program (TEXT): Program name
        - comments (TEXT): Applicant comments
        - date_added (DATE): Date the entry was posted
        - url (TEXT): Source URL from GradCafe
        - status (TEXT): Application status (Accepted, Rejected, etc.)
        - term (TEXT): Start term (e.g., 'Fall 2026')
        - us_or_international (TEXT): Citizenship status
        - gpa (REAL): Grade Point Average
        - gre (REAL): GRE total score
        - gre_v (REAL): GRE verbal score
        - gre_aw (REAL): GRE analytical writing score
        - degree (TEXT): Degree type (PhD, Masters)
        - llm_generated_program (TEXT): LLM-standardized program name
        - llm_generated_university (TEXT): LLM-standardized university name

    Args:
        conn (psycopg.Connection): Active database connection

    Returns:
        None

    Note:
        This function is idempotent - it can be called multiple times safely.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS applicants (
        p_id INTEGER PRIMARY KEY,
        program TEXT,
        comments TEXT,
        date_added DATE,
        url TEXT,
        status TEXT,
        term TEXT,
        us_or_international TEXT,
        gpa REAL,
        gre REAL,
        gre_v REAL,
        gre_aw REAL,
        degree TEXT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
    """

    cursor = conn.cursor()
    print("Creating applicants table if it doesn't exist...")
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    print("Table 'applicants' is ready.")


def load_json_data(json_file_path, conn):
    """Load applicant data from a JSON Lines file into the database.

    Reads a JSON Lines file where each line is a JSON object representing
    one applicant entry. Data is cleaned, parsed, and inserted in batches
    for efficiency. Duplicate entries (based on p_id) are automatically skipped.

    Args:
        json_file_path (str): Path to the JSON Lines file
        conn (psycopg.Connection): Active database connection

    Returns:
        int: Total number of records successfully processed

    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        psycopg.Error: If database insertion fails

    Note:
        - Data is committed in batches of 1000 records for efficiency
        - Duplicate p_id values are silently skipped (ON CONFLICT DO NOTHING)
        - Invalid entries are logged and skipped rather than causing failure

    Example:
        >>> conn = psycopg.connect(host='localhost', dbname='mydb')
        >>> records_loaded = load_json_data('applicants.json', conn)
        >>> print(f"Loaded {records_loaded} records")
    """
    cursor = conn.cursor()

    records = []
    skipped = 0
    line_num = 0

    print(f"\nReading data from {json_file_path}...")

    with open(json_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())

                # Extract p_id from URL
                p_id = extract_p_id_from_url(data.get('url'))
                if not p_id:
                    print(f"Warning: Could not extract p_id from line {line_num}, skipping.")
                    skipped += 1
                    continue

                # Map JSON fields to database columns, cleaning strings
                record = (
                    p_id,
                    clean_string(data.get('program')),
                    clean_string(data.get('comments')),
                    parse_date(data.get('date_added')),
                    clean_string(data.get('url')),
                    clean_string(data.get('applicant_status')),
                    clean_string(data.get('semester_year_start')),
                    clean_string(data.get('citizenship')),
                    parse_gpa(data.get('gpa')),
                    parse_gre_score(data.get('gre')),
                    parse_gre_score(data.get('gre_v')),
                    parse_gre_score(data.get('gre_aw')),
                    clean_string(data.get('masters_or_phd')),
                    clean_string(data.get('llm-generated-program')),
                    clean_string(data.get('llm-generated-university'))
                )

                records.append(record)

                # Batch insert every 1000 records
                if len(records) >= 1000:
                    cursor.executemany(APPLICANT_INSERT, records)
                    conn.commit()
                    print(f"Inserted {line_num - skipped} records...")
                    records = []

            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error on line {line_num}: {e}")
                skipped += 1
            except Exception as e:
                print(f"Warning: Error processing line {line_num}: {e}")
                skipped += 1

    # Insert remaining records
    if records:
        cursor.executemany(APPLICANT_INSERT, records)
        conn.commit()

    cursor.close()

    total_records = line_num - skipped
    print("\nData loading complete!")
    print(f"Total records processed: {total_records}")
    print(f"Records skipped: {skipped}")

    return total_records


def verify_data(conn):
    """Verify loaded data by displaying database statistics.

    Prints summary statistics including:
        - Total record count
        - Sample records
        - Distribution of application statuses

    Args:
        conn (psycopg.Connection): Active database connection

    Returns:
        None

    Note:
        This function only prints to stdout and doesn't modify the database.
    """
    cursor = conn.cursor()

    # Count total records
    cursor.execute("SELECT COUNT(*) FROM applicants;")
    total = cursor.fetchone()[0]
    print(f"\nTotal records in database: {total}")

    # Show sample records
    cursor.execute("SELECT * FROM applicants LIMIT 5;")
    print("\nSample records:")
    for row in cursor.fetchall():
        print(f"  p_id: {row[0]}, program: {row[1][:50]}...")

    # Show statistics by status (LIMIT caps the rows returned)
    _status_stmt = sql.SQL(
        "SELECT {status}, COUNT(*) FROM {table}"
        " WHERE {status} IS NOT NULL"
        " GROUP BY {status} ORDER BY COUNT(*) DESC"
        " LIMIT 100"
    ).format(
        table=sql.Identifier("applicants"),
        status=sql.Identifier("status"),
    )
    cursor.execute(_status_stmt)
    print("\nRecords by status:")
    for status, count in cursor.fetchall():
        print(f"  {status}: {count}")

    cursor.close()


def main():
    """Main entry point for data loading script.

    Connects to the database, creates the schema if needed, loads data from
    a JSON file, and displays verification statistics.

    Environment Variables:
        Either use DATABASE_URL (recommended)::

            DATABASE_URL=postgresql://user:password@host:port/database

        Or use individual variables::

            DB_HOST (default: localhost)
            DB_PORT (default: 5432)
            DB_NAME (default: bradleyballinger)
            DB_USER (default: bradleyballinger)
            DB_PASSWORD (default: empty string)

    Raises:
        psycopg.Error: If database connection or operations fail
        FileNotFoundError: If the data file cannot be found
        Exception: For other unexpected errors

    Note:
        The data file is expected at: ../llm_extend_applicant_data.json
        relative to this script's location.
    """
    # Path to data file in parent directory
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'llm_extend_applicant_data.json')

    try:
        # Establish connection
        conn = get_connection()

        # Create table
        create_applicants_table(conn)

        # Load data
        load_json_data(json_file_path, conn)

        # Verify data
        verify_data(conn)

        conn.close()
        print("\nConnection closed successfully.")

    except psycopg.Error as e:
        print(f"Database error: {e}")
        raise
    except FileNotFoundError:
        print(f"Error: Could not find file '{json_file_path}'")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
