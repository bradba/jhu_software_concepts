"""Flask web application for graduate school applicant analytics.

This module implements a Flask-based web dashboard that displays analytical
insights from the GradCafe applicant database. It provides both a visual
interface for viewing query results and REST API endpoints for data operations.

The application features:
    - Dashboard with 11 analytical queries
    - Live data scraping from GradCafe
    - LLM-powered data analysis updates
    - Concurrent operation management with busy-state locking

Routes:
    - GET /: Main dashboard displaying all analytics
    - POST /pull-data: Scrape new data from GradCafe and load into database
    - POST /update-analysis: Trigger LLM analysis of applicant data

Example:
    Run the application::

        python app.py

    Or with Flask CLI::

        export FLASK_APP=app.py
        flask run --port 5001

Attributes:
    app (Flask): The Flask application instance
    _busy_lock (threading.Lock): Lock for managing concurrent operations
    _is_busy (bool): Flag indicating if a background operation is running

See Also:
    - :mod:`query_data`: Database query functions used by the dashboard
    - :mod:`scrape`: Web scraping functionality
    - :mod:`load_data`: Data loading utilities
"""

import json
import os
import subprocess
import sys
import threading
from contextlib import contextmanager
from datetime import datetime

from flask import Flask, render_template, jsonify

import load_data
import query_data

app = Flask(__name__)

# Busy-state management
_busy_lock = threading.Lock()
_is_busy = False  # pylint: disable=invalid-name


def is_busy():
    """Check if the system is currently processing an operation.

    Thread-safe check for whether a background operation (scraping or
    LLM analysis) is currently running.

    Returns:
        bool: True if an operation is in progress, False otherwise

    Note:
        This is used to prevent concurrent operations that could conflict.
    """
    with _busy_lock:
        return _is_busy


@contextmanager
def busy_state():
    """Context manager for managing busy state during operations.

    Acquires the busy state at entry and releases it on exit. Prevents
    concurrent operations from interfering with each other.

    Yields:
        None

    Raises:
        RuntimeError: If system is already busy with another operation

    Example:
        >>> with busy_state():
        ...     # Perform exclusive operation
        ...     scrape_data()
    """
    global _is_busy  # pylint: disable=global-statement

    # Try to acquire busy state
    with _busy_lock:
        if _is_busy:
            raise RuntimeError("System is already busy")
        _is_busy = True

    try:
        yield
    finally:
        # Release busy state
        with _busy_lock:
            _is_busy = False


@app.route('/')
def index():
    """Render the main analytics dashboard.

    Executes all 11 analytical queries and displays results in a formatted
    web interface with JHU branding.

    Returns:
        str: Rendered HTML template with query results

    Note:
        Creates a new database connection for each request. The connection
        is properly closed after all queries complete.
    """

    # Connect to database
    conn = query_data.get_connection()

    # Run all queries and collect results
    results = {}

    # Query 1
    results['q1_count'] = query_data.question_1(conn)

    # Query 2
    results['q2_percentage'] = query_data.question_2(conn)

    # Query 3
    results['q3_averages'] = query_data.question_3(conn)

    # Query 4
    results['q4_avg_gpa'] = query_data.question_4(conn)

    # Query 5
    results['q5_percentage'] = query_data.question_5(conn)

    # Query 6
    results['q6_avg_gpa'] = query_data.question_6(conn)

    # Query 7
    results['q7_count'] = query_data.question_7(conn)

    # Query 8
    results['q8_count'] = query_data.question_8(conn)

    # Query 9
    results['q9_counts'] = query_data.question_9(conn)

    # Query 10
    results['q10_top_programs'] = query_data.question_10(conn)

    # Query 11
    results['q11_comparison'] = query_data.question_11(conn)

    # Close connection
    conn.close()

    return render_template('index.html', results=results)


@app.route('/pull-data', methods=['POST'])
def pull_data():
    """Scrape new applicant data from GradCafe and load into database.

    This endpoint orchestrates a multi-step process:
        1. Runs the web scraper to fetch recent GradCafe posts
        2. Parses and cleans the scraped data
        3. Inserts new entries into the database (skipping duplicates)
        4. Returns statistics about inserted/skipped records

    Returns:
        tuple: JSON response and HTTP status code
            - Success (200): {"status": "success", "inserted": N, "skipped": M}
            - Busy (409): {"status": "busy", "message": "..."}
            - Error (500): {"status": "error", "message": "..."}

    Raises:
        subprocess.TimeoutExpired: If scraping takes longer than 5 minutes
        RuntimeError: If system is already busy with another operation

    Note:
        - Limits scraping to 50 most recent posts by default
        - Uses ON CONFLICT to skip duplicate entries
        - Automatically cleans up temporary files
        - Thread-safe with busy-state management
    """
    # Check if system is busy
    if is_busy():
        return jsonify({
            'status': 'busy',
            'message': 'Another operation is already in progress. Please wait.'
        }), 409

    try:
        # Set busy state
        with busy_state():
            # Step 1: Run the scraper
            print("[pull-data] Starting scraper...")
            script_path = os.path.join(os.path.dirname(__file__), 'scrape.py')
            output_path = os.path.join(os.path.dirname(__file__), '..', 'new_applicant_data.json')
            scrape_result = subprocess.run(
                [sys.executable, script_path, '--limit', '50', '--out', output_path],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=False
            )

            if scrape_result.returncode != 0:
                return jsonify({
                    'status': 'error',
                    'message': f'Scraping failed: {scrape_result.stderr}'
                }), 500

            print("[pull-data] Scraping completed")

            # Step 2: Check if new data file exists
            new_data_path = os.path.join(os.path.dirname(__file__), '..', 'new_applicant_data.json')
            if not os.path.exists(new_data_path):
                return jsonify({
                    'status': 'error',
                    'message': 'No data file created by scraper'
                }), 500

            # Step 3: Load scraped data and convert to database format
            print("[pull-data] Loading new data into database...")
            with open(new_data_path, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)

            if not scraped_data:
                return jsonify({
                    'status': 'warning',
                    'message': 'No new entries found on GradCafe',
                    'count': 0
                })

            # Step 4: Insert into database using load_data functions
            conn = query_data.get_connection()

            # Convert scraped format to database format and insert
            inserted = 0
            skipped = 0

            for entry in scraped_data:
                try:
                    # Extract p_id from URL
                    p_id = load_data.extract_p_id_from_url(entry.get('url'))
                    if not p_id:
                        skipped += 1
                        continue

                    # Parse and clean data
                    record = (
                        p_id,
                        load_data.clean_string(entry.get('university', '') + ', ' + entry.get('program_name', '')),
                        load_data.clean_string(entry.get('comments')),
                        load_data.parse_date(entry.get('date_posted')),
                        load_data.clean_string(entry.get('url')),
                        load_data.clean_string(entry.get('applicant_status')),
                        load_data.clean_string(entry.get('start_term')),
                        load_data.clean_string(entry.get('citizenship')),
                        float(entry.get('gpa')) if entry.get('gpa') else None,
                        float(entry.get('gre_score')) if entry.get('gre_score') else None,
                        float(entry.get('gre_v')) if entry.get('gre_v') else None,
                        float(entry.get('gre_aw')) if entry.get('gre_aw') else None,
                        load_data.clean_string(entry.get('degree')),
                        None,  # llm_generated_program
                        None   # llm_generated_university
                    )

                    # Insert into database
                    cursor = conn.cursor()
                    insert_query = """
                        INSERT INTO applicants (
                            p_id, program, comments, date_added, url, status, term,
                            us_or_international, gpa, gre, gre_v, gre_aw, degree,
                            llm_generated_program, llm_generated_university
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (p_id) DO NOTHING;
                    """
                    cursor.execute(insert_query, record)

                    if cursor.rowcount > 0:
                        inserted += 1
                    else:
                        skipped += 1

                    cursor.close()

                except Exception as e:
                    print(f"[pull-data] Error processing entry: {e}")
                    skipped += 1
                    continue

            conn.commit()
            conn.close()

            # Clean up temporary file
            try:
                os.remove(new_data_path)
            except OSError:
                pass

            print(f"[pull-data] Completed: {inserted} inserted, {skipped} skipped")

            return jsonify({
                'status': 'success',
                'message': f'Successfully added {inserted} new entries to database',
                'inserted': inserted,
                'skipped': skipped,
                'timestamp': datetime.now().isoformat()
            })

    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Scraping timed out after 5 minutes'
        }), 500
    except RuntimeError as e:
        # Busy state error
        return jsonify({
            'status': 'busy',
            'message': str(e)
        }), 409
    except Exception as e:
        print(f"[pull-data] Error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error pulling data: {str(e)}'
        }), 500


@app.route('/update-analysis', methods=['POST'])
def update_analysis():
    """Trigger LLM-powered analysis of applicant data.

    Uses a language model to standardize university and program names,
    improving data quality for analytical queries.

    Returns:
        tuple: JSON response and HTTP status code
            - Success (200): {"status": "success", "message": "..."}
            - Busy (409): {"status": "busy", "message": "..."}
            - Error (500): {"status": "error", "message": "..."}

    Raises:
        subprocess.TimeoutExpired: If analysis takes longer than 5 minutes
        RuntimeError: If system is already busy with another operation

    Note:
        This is currently a placeholder implementation. Full LLM integration
        should be added via scripts/update_llm.py when available.
    """
    # Check if system is busy
    if is_busy():
        return jsonify({
            'status': 'busy',
            'message': 'Another operation is already in progress. Please wait.'
        }), 409

    try:
        # Set busy state
        with busy_state():
            print("[update-analysis] Starting LLM analysis update...")

            # Call LLM processing script (placeholder until update_llm.py is ready)
            # Future implementation:
            # script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'update_llm.py')
            # result = subprocess.run([sys.executable, script_path], ...)

            result = subprocess.run(
                [sys.executable, '-c', 'print("LLM analysis update placeholder")'],
                capture_output=True,
                text=True,
                timeout=300,
                check=False
            )

            if result.returncode != 0:
                return jsonify({
                    'status': 'error',
                    'message': f'LLM analysis update failed: {result.stderr}'
                }), 500

            print("[update-analysis] LLM analysis update completed")

            return jsonify({
                'status': 'success',
                'message': 'Successfully updated LLM analysis',
                'timestamp': datetime.now().isoformat()
            })

    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'LLM analysis update timed out after 5 minutes'
        }), 500
    except RuntimeError as e:
        # Busy state error
        return jsonify({
            'status': 'busy',
            'message': str(e)
        }), 409
    except Exception as e:
        print(f"[update-analysis] Error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error updating analysis: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
