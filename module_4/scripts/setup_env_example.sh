#!/bin/bash
# Example script to set up environment variables
# Copy this file to setup_env.sh and customize with your settings
# Then source it: source setup_env.sh

# Database Configuration - Option 1: Use DATABASE_URL
# export DATABASE_URL="postgresql://username:password@hostname:port/database"

# Database Configuration - Option 2: Use individual variables
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="bradleyballinger"
export DB_USER="bradleyballinger"
# export DB_PASSWORD="your_password_here"  # Uncomment and set if needed

# LLM API Configuration
export LLM_API_URL="http://localhost:8000/standardize"

# Test Database Configuration (optional - for running tests)
# export TEST_DATABASE_URL="postgresql://username:password@localhost:5432/test_db"

echo "Environment variables set:"
echo "  DB_HOST: $DB_HOST"
echo "  DB_PORT: $DB_PORT"
echo "  DB_NAME: $DB_NAME"
echo "  DB_USER: $DB_USER"
echo "  LLM_API_URL: $LLM_API_URL"
