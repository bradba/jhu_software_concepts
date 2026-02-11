"""Flask application for displaying applicant database analytics."""

from flask import Flask, render_template, jsonify
import query_data
import sys
import os
import json
import subprocess
from datetime import datetime
import threading
from contextlib import contextmanager

app = Flask(__name__)

# Busy-state management
_busy_lock = threading.Lock()
_is_busy = False


def is_busy():
    """Check if the system is currently busy with an operation."""
    global _is_busy
    with _busy_lock:
        return _is_busy


@contextmanager
def busy_state():
    """Context manager to set/unset busy state."""
    global _is_busy

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
    """Main page displaying all query results."""

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
    """
    Scrape new data from GradCafe and add it to the database.
    Returns JSON with status and message.
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
                timeout=300  # 5 minute timeout
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
            with open(new_data_path, 'r') as f:
                scraped_data = json.load(f)

            if not scraped_data:
                return jsonify({
                    'status': 'warning',
                    'message': 'No new entries found on GradCafe',
                    'count': 0
                })

            # Step 4: Insert into database using load_data functions
            import load_data
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
            except:
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
    """
    Update LLM-generated analysis for applicants in the database.
    Returns JSON with status and message.
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

            # TODO: Call LLM processing script when available
            # For now, return success with placeholder message
            # Future implementation:
            # script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'update_llm.py')
            # result = subprocess.run([sys.executable, script_path], ...)

            result = subprocess.run(
                [sys.executable, '-c', 'print("LLM analysis update placeholder")'],
                capture_output=True,
                text=True,
                timeout=300
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
