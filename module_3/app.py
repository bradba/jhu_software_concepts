"""Flask application for displaying applicant database analytics."""

from flask import Flask, render_template
import query_data

app = Flask(__name__)


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


if __name__ == '__main__':
    app.run(debug=True, port=5001)
