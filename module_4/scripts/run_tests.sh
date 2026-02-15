#!/bin/bash
# Script to run tests with optional test database configuration

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================="
echo "Running Test Suite"
echo "===================================${NC}"

# Set test database configuration (optional)
# Uncomment to use a separate test database:
# export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/test_db"
# OR use individual variables:
# export DB_NAME="test_database"

# Default test command
TEST_CMD="pytest tests/"

# Parse command line arguments
case "$1" in
    "coverage")
        echo -e "${GREEN}Running tests with coverage report${NC}"
        TEST_CMD="pytest tests/ --cov=src --cov-report=term-missing"
        ;;
    "integration")
        echo -e "${GREEN}Running integration tests only${NC}"
        TEST_CMD="pytest tests/ -m integration"
        ;;
    "unit")
        echo -e "${GREEN}Running unit tests only (excluding integration)${NC}"
        TEST_CMD="pytest tests/ -m 'not integration'"
        ;;
    "db")
        echo -e "${GREEN}Running database tests${NC}"
        TEST_CMD="pytest tests/ -m db"
        ;;
    "buttons")
        echo -e "${GREEN}Running Flask endpoint tests${NC}"
        TEST_CMD="pytest tests/ -m buttons"
        ;;
    "verbose")
        echo -e "${GREEN}Running tests in verbose mode${NC}"
        TEST_CMD="pytest tests/ -v"
        ;;
    "quick")
        echo -e "${GREEN}Running quick test (no coverage)${NC}"
        TEST_CMD="pytest tests/ -q"
        ;;
    "help")
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  coverage    - Run tests with coverage report"
        echo "  integration - Run integration tests only"
        echo "  unit        - Run unit tests only"
        echo "  db          - Run database tests"
        echo "  buttons     - Run Flask endpoint tests"
        echo "  verbose     - Run tests in verbose mode"
        echo "  quick       - Run quick test without coverage"
        echo "  help        - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh              # Run all tests"
        echo "  ./run_tests.sh coverage     # Run with coverage"
        echo "  ./run_tests.sh integration  # Run integration tests only"
        exit 0
        ;;
    "")
        echo -e "${GREEN}Running all tests${NC}"
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

echo ""
echo "Test command: $TEST_CMD"
echo ""

# Run the tests
$TEST_CMD
EXIT_CODE=$?

# Print summary
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}==================================="
    echo "✓ Tests Passed"
    echo "===================================${NC}"
else
    echo -e "\033[0;31m==================================="
    echo "✗ Tests Failed"
    echo "===================================\033[0m"
fi

exit $EXIT_CODE
