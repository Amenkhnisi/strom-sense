#!/bin/bash

# run_tests.sh
# Comprehensive test runner script

echo "🧪 Running Energy Bills API Test Suite"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest is not installed${NC}"
    echo "Install it with: pip install pytest pytest-cov pytest-asyncio httpx"
    exit 1
fi

echo -e "${GREEN}✅ pytest found${NC}"
echo ""

# Function to run tests
run_tests() {
    local test_type=$1
    local test_path=$2
    local description=$3
    
    echo -e "${YELLOW}Running $description...${NC}"
    pytest $test_path -v
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $description passed${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ $description failed${NC}"
        echo ""
        return 1
    fi
}

# Run all tests by default
if [ "$1" == "" ]; then
    echo "Running all tests..."
    echo ""
    
    # Run model tests
    run_tests "models" "tests/test_models.py" "Model Tests"
    MODEL_STATUS=$?
    
    # Run service tests
    run_tests "services" "tests/test_services.py" "Service Tests"
    SERVICE_STATUS=$?
    
    # Run API tests
    run_tests "api" "tests/test_api.py" "API Tests"
    API_STATUS=$?
    
    # Summary
    echo "======================================="
    echo "📊 Test Summary"
    echo "======================================="
    
    if [ $MODEL_STATUS -eq 0 ]; then
        echo -e "${GREEN}✅ Models: PASSED${NC}"
    else
        echo -e "${RED}❌ Models: FAILED${NC}"
    fi
    
    if [ $SERVICE_STATUS -eq 0 ]; then
        echo -e "${GREEN}✅ Services: PASSED${NC}"
    else
        echo -e "${RED}❌ Services: FAILED${NC}"
    fi
    
    if [ $API_STATUS -eq 0 ]; then
        echo -e "${GREEN}✅ API: PASSED${NC}"
    else
        echo -e "${RED}❌ API: FAILED${NC}"
    fi
    
    echo ""
    
    # Exit with error if any test failed
    if [ $MODEL_STATUS -ne 0 ] || [ $SERVICE_STATUS -ne 0 ] || [ $API_STATUS -ne 0 ]; then
        exit 1
    fi

# Run specific test suite
elif [ "$1" == "models" ]; then
    run_tests "models" "tests/test_models.py" "Model Tests"

elif [ "$1" == "services" ]; then
    run_tests "services" "tests/test_services.py" "Service Tests"

elif [ "$1" == "api" ]; then
    run_tests "api" "tests/test_api.py" "API Tests"

# Run with coverage
elif [ "$1" == "coverage" ]; then
    echo "Running tests with coverage..."
    echo ""
    pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
    echo ""
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"

# Run specific test
elif [ "$1" == "test" ] && [ "$2" != "" ]; then
    echo "Running specific test: $2"
    pytest tests/ -v -k "$2"

# Show help
else
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  (none)      Run all tests"
    echo "  models      Run model tests only"
    echo "  services    Run service tests only"
    echo "  api         Run API tests only"
    echo "  coverage    Run tests with coverage report"
    echo "  test NAME   Run specific test by name"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh"
    echo "  ./run_tests.sh models"
    echo "  ./run_tests.sh coverage"
    echo "  ./run_tests.sh test test_create_user"
fi