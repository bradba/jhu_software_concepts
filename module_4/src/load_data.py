import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
import json
import re
import os
from datetime import datetime
from urllib.parse import urlparse


def parse_gpa(gpa_str):
    """Extract numeric GPA value from string like 'GPA 3.89'."""
    if not gpa_str:
        return None
    match = re.search(r'(\d+\.?\d*)', gpa_str)
    return float(match.group(1)) if match else None


def parse_gre_score(gre_str):
    """
    Extract numeric GRE score from strings like:
    - 'GRE 327' (total)
    - 'GRE V 157' (verbal)
    - 'GRE AW 3.50' (analytical writing)
    """
    if not gre_str:
        return None
    match = re.search(r'(\d+\.?\d*)', gre_str)
    return float(match.group(1)) if match else None


def parse_date(date_str):
    """
    Parse date string like 'January 31, 2026' to date object.
    Returns None if parsing fails.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%B %d, %Y').date()
    except:
        return None


def extract_p_id_from_url(url):
    """Extract the ID from the GradCafe URL."""
    if not url:
        return None
    match = re.search(r'/result/(\d+)', url)
    return int(match.group(1)) if match else None


def clean_string(s):
    """Remove NUL characters and other problematic characters from strings."""
    if s is None:
        return None
    # Remove NUL characters (0x00) which PostgreSQL doesn't accept
    return s.replace('\x00', '')


def create_applicants_table(conn):
    """
    Create the applicants table if it doesn't exist.
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
    """
    Load data from JSON Lines file into the applicants table.
    """
    cursor = conn.cursor()

    # Prepare insert query
    insert_query = """
    INSERT INTO applicants (
        p_id, program, comments, date_added, url, status, term,
        us_or_international, gpa, gre, gre_v, gre_aw, degree,
        llm_generated_program, llm_generated_university
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (p_id) DO NOTHING;
    """

    records = []
    skipped = 0

    print(f"\nReading data from {json_file_path}...")

    with open(json_file_path, 'r') as f:
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
                    execute_batch(cursor, insert_query, records)
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
        execute_batch(cursor, insert_query, records)
        conn.commit()

    cursor.close()

    total_records = line_num - skipped
    print(f"\nData loading complete!")
    print(f"Total records processed: {total_records}")
    print(f"Records skipped: {skipped}")

    return total_records


def verify_data(conn):
    """
    Verify the loaded data by showing some statistics.
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

    # Show statistics by status
    cursor.execute("""
        SELECT status, COUNT(*)
        FROM applicants
        WHERE status IS NOT NULL
        GROUP BY status
        ORDER BY COUNT(*) DESC;
    """)
    print("\nRecords by status:")
    for status, count in cursor.fetchall():
        print(f"  {status}: {count}")

    cursor.close()


def main():
    """
    Main function to create table and load data.

    Uses DATABASE_URL environment variable if set (format: postgresql://user:password@host:port/database)
    Otherwise uses individual environment variables or defaults:
    - DB_HOST (default: localhost)
    - DB_PORT (default: 5432)
    - DB_NAME (default: bradleyballinger)
    - DB_USER (default: bradleyballinger)
    - DB_PASSWORD (default: empty)
    """
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Parse DATABASE_URL
        parsed = urlparse(database_url)
        conn_params = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/') if parsed.path else 'bradleyballinger',
            'user': parsed.username or 'bradleyballinger',
        }
        if parsed.password:
            conn_params['password'] = parsed.password
    else:
        # Use individual environment variables or defaults
        conn_params = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': int(os.environ.get('DB_PORT', '5432')),
            'database': os.environ.get('DB_NAME', 'bradleyballinger'),
            'user': os.environ.get('DB_USER', 'bradleyballinger'),
        }
        if os.environ.get('DB_PASSWORD'):
            conn_params['password'] = os.environ.get('DB_PASSWORD')

    # Path to data file in parent directory
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'llm_extend_applicant_data.json')

    try:
        # Establish connection
        print(f"Connecting to database '{conn_params['database']}' at {conn_params['host']}:{conn_params['port']}...")
        conn = psycopg2.connect(**conn_params)

        # Create table
        create_applicants_table(conn)

        # Load data
        load_json_data(json_file_path, conn)

        # Verify data
        verify_data(conn)

        conn.close()
        print("\nConnection closed successfully.")

    except psycopg2.Error as e:
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
