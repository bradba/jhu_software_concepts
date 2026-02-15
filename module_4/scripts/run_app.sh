#!/bin/bash
# Script to run the Flask application with environment variables

# Set default database configuration if not already set
export DB_HOST="${DB_HOST:-localhost}"
export DB_PORT="${DB_PORT:-5432}"
export DB_NAME="${DB_NAME:-bradleyballinger}"
export DB_USER="${DB_USER:-bradleyballinger}"
# export DB_PASSWORD="${DB_PASSWORD:-}"

# Alternatively, use DATABASE_URL (uncomment to use):
# export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Set LLM API URL
export LLM_API_URL="${LLM_API_URL:-http://localhost:8000/standardize}"

# Print configuration
echo "==================================="
echo "Starting Flask Application"
echo "==================================="
echo "Database: ${DB_NAME}"
echo "Host: ${DB_HOST}:${DB_PORT}"
echo "User: ${DB_USER}"
echo "LLM API: ${LLM_API_URL}"
echo "==================================="
echo ""

# Run the Flask app
python src/app.py
