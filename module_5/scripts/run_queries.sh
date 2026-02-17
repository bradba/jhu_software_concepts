#!/bin/bash
# Script to run database queries with environment variables

# Set default database configuration if not already set
export DB_HOST="${DB_HOST:-localhost}"
export DB_PORT="${DB_PORT:-5432}"
export DB_NAME="${DB_NAME:-bradleyballinger}"
export DB_USER="${DB_USER:-bradleyballinger}"
# export DB_PASSWORD="${DB_PASSWORD:-}"

# Alternatively, use DATABASE_URL (uncomment to use):
# export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Print configuration
echo "==================================="
echo "Running Database Queries"
echo "==================================="
echo "Database: ${DB_NAME}"
echo "Host: ${DB_HOST}:${DB_PORT}"
echo "User: ${DB_USER}"
echo "==================================="
echo ""

# Run the queries
python src/query_data.py
