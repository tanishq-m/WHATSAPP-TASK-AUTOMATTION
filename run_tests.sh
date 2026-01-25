#!/bin/bash

# ============================================================================
# Test Runner Script for WhatsApp Task Manager
# ============================================================================
# 
# Usage:
#   ./run_tests.sh           # Run all tests
#   ./run_tests.sh backend   # Run only backend tests
#   ./run_tests.sh frontend  # Run only frontend tests
#   ./run_tests.sh coverage  # Run all tests with coverage
#
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         WhatsApp Task Manager - Test Suite                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Navigate to project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Function to run backend tests
run_backend_tests() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  Running Backend Tests (Python/Flask)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Activate virtual environment if it exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    cd backend
    
    if [ "$1" == "coverage" ]; then
        python -m pytest test_api.py -v --cov=. --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated: backend/htmlcov/index.html${NC}"
    else
        python -m pytest test_api.py -v
    fi
    
    cd ..
}

# Function to run frontend tests
run_frontend_tests() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  Running Frontend Tests (React/Vitest)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ "$1" == "coverage" ]; then
        npm run test:coverage
    else
        npm test -- --run
    fi
}

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    # Check Python dependencies
    if ! command -v pytest &> /dev/null; then
        echo -e "${YELLOW}Installing pytest...${NC}"
        pip install pytest pytest-cov
    fi
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing npm dependencies...${NC}"
        npm install
    fi
    
    # Check if vitest is installed
    if ! npm list vitest &> /dev/null; then
        echo -e "${YELLOW}Installing test dependencies...${NC}"
        npm install
    fi
    
    echo -e "${GREEN}Dependencies OK${NC}"
    echo ""
}

# Main execution
case "$1" in
    "backend")
        check_dependencies
        run_backend_tests $2
        ;;
    "frontend")
        check_dependencies
        run_frontend_tests $2
        ;;
    "coverage")
        check_dependencies
        run_backend_tests coverage
        run_frontend_tests coverage
        ;;
    *)
        check_dependencies
        run_backend_tests
        run_frontend_tests
        ;;
esac

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    All Tests Completed!                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
