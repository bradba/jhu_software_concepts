"""Shared database connection utility.

Provides a single :func:`get_connection` function used by both
:mod:`load_data` and :mod:`query_data` to avoid duplicating connection
parameter logic.
"""

import os
from urllib.parse import urlparse

import psycopg


def get_connection():
    """Create and return a database connection.

    Uses DATABASE_URL environment variable if set (format:
    ``postgresql://user:password@host:port/database``).  Otherwise falls back
    to individual environment variables or built-in defaults.

    Environment Variables:
        DATABASE_URL: Full connection URL (takes precedence)
        DB_HOST: Database host (default: localhost)
        DB_PORT: Database port (default: 5432)
        DB_NAME: Database name (default: bradleyballinger)
        DB_USER: Database user (default: bradleyballinger)
        DB_PASSWORD: Database password (default: empty)

    Returns:
        psycopg.Connection: Open database connection.
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
