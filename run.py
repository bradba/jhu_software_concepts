"""Run script for the portfolio Flask app.

Usage: `python run.py`
Supports environment variables `HOST` and `PORT` (defaults to 127.0.0.1:8080).
"""
import os

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    # Import the app from the module_1 package
    from module_1.app import app

    app.run(debug=True, host=host, port=port)
