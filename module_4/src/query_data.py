import psycopg
from psycopg import sql
import os
from urllib.parse import urlparse


def get_connection():
    """Create and return a database connection.

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
        # Parse DATABASE_URL (e.g., postgresql://user:password@host:port/database)
        parsed = urlparse(database_url)
        conn_params = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'dbname': parsed.path.lstrip('/') if parsed.path else 'bradleyballinger',
            'user': parsed.username or 'bradleyballinger',
        }
        if parsed.password:
            conn_params['password'] = parsed.password
    else:
        # Use individual environment variables or defaults
        conn_params = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': int(os.environ.get('DB_PORT', '5432')),
            'dbname': os.environ.get('DB_NAME', 'bradleyballinger'),
            'user': os.environ.get('DB_USER', 'bradleyballinger'),
        }
        if os.environ.get('DB_PASSWORD'):
            conn_params['password'] = os.environ.get('DB_PASSWORD')

    return psycopg.connect(**conn_params)


def question_1(conn):
    """How many entries do you have in your database who have applied for Fall 2026?"""
    cursor = conn.cursor()
    query = """
        SELECT COUNT(*)
        FROM applicants
        WHERE term = 'Fall 2026';
    """
    cursor.execute(query)
    count = cursor.fetchone()[0]
    cursor.close()

    print("Question 1: How many entries applied for Fall 2026?")
    print(f"Answer: {count:,} entries\n")
    return count


def question_2(conn):
    """What percentage of entries are from international students (not American or Other)?"""
    cursor = conn.cursor()

    # Total entries
    cursor.execute("SELECT COUNT(*) FROM applicants WHERE us_or_international IS NOT NULL;")
    total = cursor.fetchone()[0]

    # International students (not American or Other)
    cursor.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE us_or_international = 'International';
    """)
    international = cursor.fetchone()[0]

    percentage = (international / total * 100) if total > 0 else 0
    cursor.close()

    print("Question 2: What percentage of entries are from international students?")
    print(f"Answer: {percentage:.2f}%")
    print(f"  (International: {international:,} out of {total:,} total entries)\n")
    return percentage


def question_3(conn):
    """What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?"""
    cursor = conn.cursor()

    # Get averages for each metric
    query = """
        SELECT
            AVG(gpa) as avg_gpa,
            COUNT(gpa) as gpa_count,
            AVG(gre) as avg_gre,
            COUNT(gre) as gre_count,
            AVG(gre_v) as avg_gre_v,
            COUNT(gre_v) as gre_v_count,
            AVG(gre_aw) as avg_gre_aw,
            COUNT(gre_aw) as gre_aw_count
        FROM applicants
        WHERE gpa IS NOT NULL
           OR gre IS NOT NULL
           OR gre_v IS NOT NULL
           OR gre_aw IS NOT NULL;
    """
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()

    print("Question 3: Average scores of applicants who provide these metrics:")
    print(f"  Average GPA: {result[0]:.2f} (from {result[1]:,} entries)")
    print(f"  Average GRE: {result[2]:.2f} (from {result[3]:,} entries)")
    print(f"  Average GRE V: {result[4]:.2f} (from {result[5]:,} entries)")
    print(f"  Average GRE AW: {result[6]:.2f} (from {result[7]:,} entries)\n")

    return {
        'avg_gpa': result[0],
        'avg_gre': result[2],
        'avg_gre_v': result[4],
        'avg_gre_aw': result[6]
    }


def question_4(conn):
    """What is the average GPA of American students in Fall 2026?"""
    cursor = conn.cursor()

    query = """
        SELECT AVG(gpa), COUNT(gpa)
        FROM applicants
        WHERE term = 'Fall 2026'
          AND us_or_international = 'American'
          AND gpa IS NOT NULL;
    """
    cursor.execute(query)
    avg_gpa, count = cursor.fetchone()
    cursor.close()

    print("Question 4: Average GPA of American students in Fall 2026:")
    print(f"Answer: {avg_gpa:.2f} (from {count:,} entries with GPA data)\n")
    return avg_gpa


def question_5(conn):
    """What percent of entries for Fall 2026 are Acceptances?"""
    cursor = conn.cursor()

    # Total Fall 2026 entries
    cursor.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term = 'Fall 2026';
    """)
    total = cursor.fetchone()[0]

    # Acceptances for Fall 2026
    cursor.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term = 'Fall 2026'
          AND status = 'Accepted';
    """)
    acceptances = cursor.fetchone()[0]

    percentage = (acceptances / total * 100) if total > 0 else 0
    cursor.close()

    print("Question 5: What percent of Fall 2026 entries are Acceptances?")
    print(f"Answer: {percentage:.2f}%")
    print(f"  (Accepted: {acceptances:,} out of {total:,} Fall 2026 entries)\n")
    return percentage


def question_6(conn):
    """What is the average GPA of applicants who applied for Fall 2026 who are Acceptances?"""
    cursor = conn.cursor()

    query = """
        SELECT AVG(gpa), COUNT(gpa)
        FROM applicants
        WHERE term = 'Fall 2026'
          AND status = 'Accepted'
          AND gpa IS NOT NULL;
    """
    cursor.execute(query)
    avg_gpa, count = cursor.fetchone()
    cursor.close()

    print("Question 6: Average GPA of Fall 2026 acceptances:")
    print(f"Answer: {avg_gpa:.2f} (from {count:,} accepted entries with GPA data)\n")
    return avg_gpa


def question_7(conn):
    """How many entries are from applicants who applied to JHU for a masters degree in Computer Science?"""
    cursor = conn.cursor()

    query = """
        SELECT COUNT(*)
        FROM applicants
        WHERE (program ILIKE '%Johns Hopkins%' OR program ILIKE '%JHU%')
          AND program ILIKE '%Computer Science%'
          AND degree = 'Masters';
    """
    cursor.execute(query)
    count = cursor.fetchone()[0]
    cursor.close()

    print("Question 7: Entries for JHU Masters in Computer Science:")
    print(f"Answer: {count:,} entries\n")
    return count


def question_8(conn):
    """How many entries from 2026 are acceptances from Georgetown, MIT, Stanford, CMU for PhD CS?"""
    cursor = conn.cursor()

    # Using original downloaded fields
    query = """
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%2026%'
          AND status = 'Accepted'
          AND degree = 'PhD'
          AND program ILIKE '%Computer Science%'
          AND (
              program ILIKE '%Georgetown%' OR
              program ILIKE '%MIT%' OR
              program ILIKE '%Stanford%' OR
              program ILIKE '%Carnegie Mellon%' OR
              program ILIKE '%CMU%'
          );
    """
    cursor.execute(query)
    count_original = cursor.fetchone()[0]
    cursor.close()

    print("Question 8: 2026 acceptances from Georgetown/MIT/Stanford/CMU for PhD CS:")
    print(f"Answer (using original program field): {count_original:,} entries\n")
    return count_original


def question_9(conn):
    """Do numbers for question 8 change if you use LLM Generated Fields?"""
    cursor = conn.cursor()

    # Using LLM-generated fields
    query = """
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%2026%'
          AND status = 'Accepted'
          AND degree = 'PhD'
          AND llm_generated_program ILIKE '%Computer Science%'
          AND (
              llm_generated_university ILIKE '%Georgetown%' OR
              llm_generated_university ILIKE '%MIT%' OR
              llm_generated_university ILIKE '%Stanford%' OR
              llm_generated_university ILIKE '%Carnegie Mellon%' OR
              llm_generated_university ILIKE '%CMU%'
          );
    """
    cursor.execute(query)
    count_llm = cursor.fetchone()[0]

    # Get original count for comparison
    cursor.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%2026%'
          AND status = 'Accepted'
          AND degree = 'PhD'
          AND program ILIKE '%Computer Science%'
          AND (
              program ILIKE '%Georgetown%' OR
              program ILIKE '%MIT%' OR
              program ILIKE '%Stanford%' OR
              program ILIKE '%Carnegie Mellon%' OR
              program ILIKE '%CMU%'
          );
    """)
    count_original = cursor.fetchone()[0]

    cursor.close()

    print("Question 9: Does question 8 change with LLM-generated fields?")
    print(f"Answer (using LLM-generated fields): {count_llm:,} entries")
    print(f"Answer (using original fields): {count_original:,} entries")

    if count_llm != count_original:
        difference = count_llm - count_original
        print(f"Difference: {difference:+,} entries")
        print(f"The LLM-generated fields {'found more' if difference > 0 else 'found fewer'} matches.\n")
    else:
        print("The numbers are the same.\n")

    return count_llm, count_original


def question_10(conn):
    """What are the top 10 most applied-to programs for Fall 2026?"""
    cursor = conn.cursor()

    query = """
        SELECT
            llm_generated_university,
            llm_generated_program,
            COUNT(*) as total_applications,
            SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) as acceptances,
            ROUND(100.0 * SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*), 2) as acceptance_rate
        FROM applicants
        WHERE term = 'Fall 2026'
            AND llm_generated_university IS NOT NULL
            AND llm_generated_program IS NOT NULL
        GROUP BY llm_generated_university, llm_generated_program
        ORDER BY total_applications DESC
        LIMIT 10;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()

    print("Question 10: Top 10 most applied-to programs for Fall 2026:")
    print(f"{'Rank':<6}{'University':<40}{'Program':<30}{'Apps':<8}{'Accept Rate':<12}")
    print("-" * 96)

    for i, (university, program, total, acceptances, rate) in enumerate(results, 1):
        print(f"{i:<6}{university[:39]:<40}{program[:29]:<30}{total:<8}{rate:.2f}%")

    print()
    return results


def question_11(conn):
    """How do acceptance rates compare between PhD and Masters programs?"""
    cursor = conn.cursor()

    query = """
        SELECT
            degree,
            COUNT(*) as total_applications,
            SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) as acceptances,
            ROUND(100.0 * SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*), 2) as acceptance_rate,
            ROUND(CAST(AVG(CASE WHEN status = 'Accepted' AND gpa IS NOT NULL THEN gpa END) AS numeric), 2) as avg_gpa_accepted,
            COUNT(CASE WHEN status = 'Accepted' AND gpa IS NOT NULL THEN 1 END) as gpa_count
        FROM applicants
        WHERE degree IN ('PhD', 'Masters')
        GROUP BY degree
        ORDER BY degree;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()

    print("Question 11: PhD vs Masters program comparison:")
    print(f"{'Degree':<10}{'Total Apps':<12}{'Acceptances':<12}{'Accept Rate':<14}{'Avg GPA (Accepted)':<20}")
    print("-" * 68)

    for degree, total, acceptances, rate, avg_gpa, gpa_count in results:
        gpa_str = f"{avg_gpa:.2f} (n={gpa_count:,})" if avg_gpa else "N/A"
        total_str = f"{total:,}"
        accept_str = f"{acceptances:,}"
        print(f"{degree:<10}{total_str:<12}{accept_str:<12}{rate:.2f}%{' ':<10}{gpa_str:<20}")

    print()
    return results


def main():
    """Run all queries and display results."""
    print("=" * 80)
    print("APPLICANT DATABASE QUERIES")
    print("=" * 80)
    print()

    try:
        conn = get_connection()
        print(f"Connected to database successfully.\n")

        # Run all questions
        question_1(conn)
        question_2(conn)
        question_3(conn)
        question_4(conn)
        question_5(conn)
        question_6(conn)
        question_7(conn)
        question_8(conn)
        question_9(conn)
        question_10(conn)
        question_11(conn)

        conn.close()
        print("=" * 80)
        print("All queries completed successfully!")
        print("=" * 80)

    except psycopg.Error as e:
        print(f"Database error: {e}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
