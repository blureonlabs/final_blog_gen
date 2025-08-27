#!/bin/bash

# 🔍 Blu Blog Gen - Health Check Script
# This script checks the health status of all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local timeout=${2:-5}
    
    if curl -s --max-time $timeout "$url" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check Redis
check_redis() {
    echo -n "Redis: "
    if redis-cli ping >/dev/null 2>&1; then
        print_success "Running and responding"
        return 0
    else
        print_error "Not running or not responding"
        return 1
    fi
}

# Function to check Backend API
check_backend() {
    echo -n "Backend API: "
    if check_port 8000; then
        if check_http "http://localhost:8000/health"; then
            print_success "Running on port 8000 and responding"
            return 0
        else
            print_warning "Running on port 8000 but health check failed"
            return 1
        fi
    else
        print_error "Not running on port 8000"
        return 1
    fi
}

# Function to check Frontend
check_frontend() {
    echo -n "Frontend: "
    if check_port 3000; then
        if check_http "http://localhost:3000"; then
            print_success "Running on port 3000 and responding"
            return 0
        else
            print_warning "Running on port 3000 but not responding"
            return 1
        fi
    else
        print_error "Not running on port 3000"
        return 1
    fi
}

# Function to check Celery Worker
check_celery() {
    echo -n "Celery Worker: "
    if command -v celery >/dev/null 2>&1; then
        # Change to backend directory to check Celery
        cd backend 2>/dev/null || {
            print_error "Cannot access backend directory"
            return 1
        }
        
        # Activate virtual environment if it exists
        if [ -d "venv" ]; then
            source venv/bin/activate 2>/dev/null || true
        fi
        
        # Check if Celery is responding
        if celery -A core.celery_app inspect active >/dev/null 2>&1; then
            print_success "Running and responding"
            cd ..
            return 0
        else
            print_warning "Running but not responding to inspect command"
            cd ..
            return 1
        fi
    else
        print_error "Celery command not found"
        return 1
    fi
}

# Function to check environment files
check_environment() {
    echo -n "Environment Files: "
    local missing_files=()
    
    # Check frontend environment
    if [ ! -f ".env.local" ]; then
        missing_files+=(".env.local")
    fi
    
    # Check backend environment
    if [ ! -f "backend/.env" ]; then
        missing_files+=("backend/.env")
    fi
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        print_success "All environment files present"
        return 0
    else
        print_warning "Missing environment files: ${missing_files[*]}"
        return 1
    fi
}

# Function to check dependencies
check_dependencies() {
    echo -n "Dependencies: "
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        missing_deps+=("Python")
    fi
    
    # Check Node.js
    if ! command -v node >/dev/null 2>&1; then
        missing_deps+=("Node.js")
    fi
    
    # Check npm
    if ! command -v npm >/dev/null 2>&1; then
        missing_deps+=("npm")
    fi
    
    # Check Redis
    if ! command -v redis-cli >/dev/null 2>&1; then
        missing_deps+=("Redis")
    fi
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        print_success "All required dependencies installed"
        return 0
    else
        print_error "Missing dependencies: ${missing_deps[*]}"
        return 1
    fi
}

# Function to check virtual environment
check_venv() {
    echo -n "Python Virtual Environment: "
    if [ -d "backend/venv" ]; then
        if [ -f "backend/venv/bin/activate" ] || [ -f "backend/venv/Scripts/activate.bat" ]; then
            print_success "Virtual environment exists"
            return 0
        else
            print_warning "Virtual environment exists but activation script missing"
            return 1
        fi
    else
        print_warning "Virtual environment not found"
        return 1
    fi
}

# Function to check node modules
check_node_modules() {
    echo -n "Node.js Dependencies: "
    if [ -d "node_modules" ]; then
        print_success "Node modules installed"
        return 0
    else
        print_warning "Node modules not installed"
        return 1
    fi
}

# Function to check API endpoints
check_api_endpoints() {
    echo -n "API Endpoints: "
    local failed_endpoints=()
    
    # Check main API
    if ! check_http "http://localhost:8000"; then
        failed_endpoints+=("Main API")
    fi
    
    # Check health endpoint
    if ! check_http "http://localhost:8000/health"; then
        failed_endpoints+=("Health")
    fi
    
    # Check docs endpoint
    if ! check_http "http://localhost:8000/docs"; then
        failed_endpoints+=("Docs")
    fi
    
    if [ ${#failed_endpoints[@]} -eq 0 ]; then
        print_success "All API endpoints responding"
        return 0
    else
        print_warning "Failed endpoints: ${failed_endpoints[*]}"
        return 1
    fi
}

# Function to get service status summary
get_status_summary() {
    local total_checks=8
    local passed_checks=0
    
    # Count passed checks
    if check_redis >/dev/null; then ((passed_checks++)); fi
    if check_backend >/dev/null; then ((passed_checks++)); fi
    if check_frontend >/dev/null; then ((passed_checks++)); fi
    if check_celery >/dev/null; then ((passed_checks++)); fi
    if check_environment >/dev/null; then ((passed_checks++)); fi
    if check_dependencies >/dev/null; then ((passed_checks++)); fi
    if check_venv >/dev/null; then ((passed_checks++)); fi
    if check_node_modules >/dev/null; then ((passed_checks++)); fi
    
    echo ""
    echo "======================================"
    echo "📊 Health Check Summary"
    echo "======================================"
    echo "Total Checks: $total_checks"
    echo "Passed: $passed_checks"
    echo "Failed: $((total_checks - passed_checks))"
    echo "Success Rate: $((passed_checks * 100 / total_checks))%"
    
    if [ $passed_checks -eq $total_checks ]; then
        print_success "All systems operational! 🎉"
    elif [ $passed_checks -ge $((total_checks * 3 / 4)) ]; then
        print_warning "Most systems operational, some issues detected"
    else
        print_error "Multiple systems down, immediate attention required"
    fi
}

# Main execution
main() {
    echo "🔍 Health Check - Blu Blog Gen Services"
    echo "======================================"
    echo "Timestamp: $(date)"
    echo "Working Directory: $(pwd)"
    echo ""
    
    # Run all health checks
    check_dependencies
    check_environment
    check_venv
    check_node_modules
    check_redis
    check_backend
    check_frontend
    check_celery
    check_api_endpoints
    
    # Show summary
    get_status_summary
    
    echo ""
    echo "🔍 Detailed Status:"
    echo "  Redis:        redis-cli ping"
    echo "  Backend:      curl http://localhost:8000/health"
    echo "  Frontend:     curl http://localhost:3000"
    echo "  Celery:       cd backend && source venv/bin/activate && celery -A core.celery_app inspect active"
    echo ""
    echo "📚 Documentation: http://localhost:8000/docs"
    echo "🏥 Health Check: http://localhost:8000/health"
}

# Run main function
main "$@"
