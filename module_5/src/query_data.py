"""Database query module for analyzing graduate school applicant data.

This module provides a comprehensive set of analytical queries for the applicant
database. It includes utilities for connecting to PostgreSQL and executing
various statistical and analytical queries on the graduate school application data.

The module is designed to answer key questions about:
    - Application volumes and trends
    - Demographic distributions
    - Acceptance rates and selectivity
    - Academic metrics (GPA, GRE scores)
    - Program-specific statistics

Example:
    Basic usage::

        import query_data

        conn = query_data.get_connection()
        fall_2026_count = query_data.question_1(conn)
        international_pct = query_data.question_2(conn)
        conn.close()

Attributes:
    None

See Also:
    - :mod:`load_data`: For loading data into the database
    - :mod:`app`: For the Flask web interface
"""

import psycopg
from psycopg import sql

from db import get_connection

# Hard ceiling on caller-supplied LIMIT values (clamp to 1–_LIMIT_MAX).
_LIMIT_MAX = 100


def question_1(conn):
    """Count entries for Fall 2026 applications.

    Args:
        conn (psycopg.Connection): Active database connection

    Returns:
        int: Number of Fall 2026 application entries

    Example:
        >>> conn = get_connection()
        >>> count = question_1(conn)
        >>> print(f"Fall 2026 applications: {count}")
    """
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
    """Calculate percentage of international student applications.

    Args:
        conn (psycopg.Connection): Active database connection

    Returns:
        float: Percentage of entries from international students (0-100)

    Note:
        Only counts entries where citizenship status is explicitly 'International',
        excluding American and other categories.

    Example:
        >>> conn = get_connection()
        >>> pct = question_2(conn)
        >>> print(f"International students: {pct:.2f}%")
    """
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
    """Calculate average academic metrics across all applicants.

    Computes mean values for GPA and GRE scores among applicants who
    provided these metrics.

    Args:
        conn (psycopg.Connection): Active database connection

    Returns:
        dict: Dictionary containing:
            - avg_gpa (float): Average GPA
            - avg_gre (float): Average total GRE score
            - avg_gre_v (float): Average GRE verbal score
            - avg_gre_aw (float): Average GRE analytical writing score

    Note:
        Only includes non-null values in the averages. The number of
        entries contributing to each average may differ.

    Example:
        >>> conn = get_connection()
        >>> metrics = question_3(conn)
        >>> print(f"Average GPA: {metrics['avg_gpa']:.2f}")
    """
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
    """Calculate average GPA for American students applying to Fall 2026.

    Args:
        conn (psycopg.Connection): Active database connection

    Returns:
        float: Average GPA of American students for Fall 2026

    Note:
        Only includes entries with:
            - term = 'Fall 2026'
            - us_or_international = 'American'
            - Non-null GPA value

    Example:
        >>> conn = get_connection()
        >>> avg_gpa = question_4(conn)
        >>> print(f"American students avg GPA: {avg_gpa:.2f}")
    """
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


def question_10(conn, limit=10):
    """Find the top N most popular programs for Fall 2026.

    Ranks programs by application volume and calculates acceptance rates.

    Args:
        conn (psycopg.Connection): Active database connection
        limit (int): Maximum rows to return; clamped to 1–100 (default: 10)

    Returns:
        list of tuple: Each tuple contains:
            - university (str): Standardized university name
            - program (str): Standardized program name
            - total_applications (int): Number of applications
            - acceptances (int): Number of acceptances
            - acceptance_rate (float): Percentage accepted (0-100)

    Note:
        Uses LLM-generated standardized university and program names for
        better aggregation of similar programs.

    Example:
        >>> conn = get_connection()
        >>> top_programs = question_10(conn)
        >>> for uni, prog, apps, acc, rate in top_programs:
        ...     print(f"{uni} - {prog}: {apps} applications")
    """
    # Enforce maximum: caller cannot request more than _LIMIT_MAX rows.
    limit = max(1, min(int(limit), _LIMIT_MAX))

    cursor = conn.cursor()

    # SQL statement constructed with sql.SQL so identifiers are quoted by the
    # driver.  The LIMIT value is passed as a parameter (%s) — never embedded
    # in the SQL text — so the driver handles type safety.
    stmt = sql.SQL("""
        SELECT
            {univ},
            {prog},
            COUNT(*) AS total_applications,
            SUM(CASE WHEN {status} = 'Accepted' THEN 1 ELSE 0 END) AS acceptances,
            ROUND(
                100.0 * SUM(CASE WHEN {status} = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS acceptance_rate
        FROM {table}
        WHERE {term} = 'Fall 2026'
            AND {univ} IS NOT NULL
            AND {prog} IS NOT NULL
        GROUP BY {univ}, {prog}
        ORDER BY total_applications DESC
        LIMIT {lim}
    """).format(
        table=sql.Identifier("applicants"),
        univ=sql.Identifier("llm_generated_university"),
        prog=sql.Identifier("llm_generated_program"),
        status=sql.Identifier("status"),
        term=sql.Identifier("term"),
        lim=sql.Placeholder(),
    )
    cursor.execute(stmt, [limit])
    results = cursor.fetchall()
    cursor.close()

    print("Question 10: Top 10 most applied-to programs for Fall 2026:")
    print(f"{'Rank':<6}{'University':<40}{'Program':<30}{'Apps':<8}{'Accept Rate':<12}")
    print("-" * 96)

    for i, (university, program, total, _acceptances, rate) in enumerate(results, 1):
        print(f"{i:<6}{university[:39]:<40}{program[:29]:<30}{total:<8}{rate:.2f}%")

    print()
    return results


def question_11(conn):
    """How do acceptance rates compare between PhD and Masters programs?"""
    cursor = conn.cursor()

    # Identifiers are quoted via sql.SQL so any future rename stays safe.
    # LIMIT 100 provides an inherent upper bound on rows returned.
    stmt = sql.SQL("""
        SELECT
            {degree},
            COUNT(*) AS total_applications,
            SUM(CASE WHEN {status} = 'Accepted' THEN 1 ELSE 0 END) AS acceptances,
            ROUND(
                100.0 * SUM(CASE WHEN {status} = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS acceptance_rate,
            ROUND(
                CAST(
                    AVG(CASE WHEN {status} = 'Accepted' AND {gpa} IS NOT NULL THEN {gpa} END)
                    AS numeric
                ),
                2
            ) AS avg_gpa_accepted,
            COUNT(CASE WHEN {status} = 'Accepted' AND {gpa} IS NOT NULL THEN 1 END) AS gpa_count
        FROM {table}
        WHERE {degree} IN ('PhD', 'Masters')
        GROUP BY {degree}
        ORDER BY {degree}
        LIMIT 100
    """).format(
        table=sql.Identifier("applicants"),
        degree=sql.Identifier("degree"),
        status=sql.Identifier("status"),
        gpa=sql.Identifier("gpa"),
    )
    cursor.execute(stmt)
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
    """Execute all analytical queries and display results.

    Runs all 11 analytical queries in sequence and prints formatted results
    to stdout. Handles database connection setup and teardown.

    Returns:
        None

    Raises:
        psycopg.Error: If database connection or query execution fails
        Exception: For other unexpected errors

    Example:
        Run from command line::

            python query_data.py

    Note:
        Database connection parameters are read from environment variables.
        See :func:`get_connection` for details.
    """
    print("=" * 80)
    print("APPLICANT DATABASE QUERIES")
    print("=" * 80)
    print()

    try:
        conn = get_connection()
        print("Connected to database successfully.\n")

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
