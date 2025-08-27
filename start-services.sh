#!/bin/bash

# 🚀 Blu Blog Gen - Service Startup Script
# This script starts all required services for the blog generation system

set -e  # Exit on any error

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            print_success "$service_name is ready on port $port"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start on port $port after $max_attempts attempts"
    return 1
}

# Function to cleanup on exit
cleanup() {
    print_status "🛑 Stopping all services..."
    
    # Kill background processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend stopped"
    fi
    
    if [ ! -z "$CELERY_PID" ]; then
        kill $CELERY_PID 2>/dev/null || true
        print_status "Celery worker stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Frontend stopped"
    fi
    
    # Stop Redis if we started it
    if [ "$REDIS_STARTED" = true ]; then
        brew services stop redis 2>/dev/null || true
        print_status "Redis stopped"
    fi
    
    print_success "All services stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup INT TERM

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "🚀 Starting Blu Blog Gen Services..."
print_status "Working directory: $SCRIPT_DIR"

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

if ! command_exists npm; then
    print_error "Node.js/npm is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command_exists redis-cli; then
    print_error "Redis is not installed. Please install Redis first."
    print_status "Installation commands:"
    print_status "  macOS: brew install redis"
    print_status "  Linux: sudo apt-get install redis-server"
    exit 1
fi

print_success "Prerequisites check passed"

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Start Redis
print_status "📡 Starting Redis..."
if ! redis-cli ping >/dev/null 2>&1; then
    if command_exists brew; then
        brew services start redis
        REDIS_STARTED=true
        sleep 3
    else
        print_error "Redis is not running and brew is not available. Please start Redis manually."
        exit 1
    fi
else
    print_success "Redis is already running"
fi

# Verify Redis is working
if redis-cli ping >/dev/null 2>&1; then
    print_success "Redis is running and responding"
else
    print_error "Redis failed to start or is not responding"
    exit 1
fi

# Start Backend
print_status "🔧 Starting Backend API..."
cd backend

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if [ ! -f "requirements_installed" ]; then
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    touch requirements_installed
fi

# Check if backend is already running
if check_port 8000; then
    print_warning "Backend is already running on port 8000"
else
    # Start backend in background
    python start_server.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    print_status "Backend started with PID: $BACKEND_PID"
    
    # Wait for backend to be ready
    wait_for_service "Backend API" 8000
fi

cd ..

# Start Celery Worker
print_status "⚡ Starting Celery Worker..."
cd backend
source venv/bin/activate

# Check if Celery is already running
if celery -A core.celery_app inspect active >/dev/null 2>&1; then
    print_warning "Celery worker is already running"
else
    # Start Celery worker in background
    celery -A core.celery_app worker --loglevel=info --queues=wordpress_publishing,content_generation,blog_formatting,image_generation > ../celery.log 2>&1 &
    CELERY_PID=$!
    print_status "Celery worker started with PID: $CELERY_PID"
    
    # Wait a bit for Celery to initialize
    sleep 5
    
    # Check if Celery is working
    if celery -A core.celery_app inspect active >/dev/null 2>&1; then
        print_success "Celery worker is running and responding"
    else
        print_warning "Celery worker may not be fully initialized yet"
    fi
fi

cd ..

# Start Frontend
print_status "🎨 Starting Frontend..."
cd "$SCRIPT_DIR"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_status "Installing Node.js dependencies..."
    npm install
fi

# Check if frontend is already running
if check_port 3000; then
    print_warning "Frontend is already running on port 3000"
else
    # Start frontend in background
    npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    print_status "Frontend started with PID: $FRONTEND_PID"
    
    # Wait for frontend to be ready
    wait_for_service "Frontend" 3000
fi

# Final status
echo ""
print_success "✅ All services started successfully!"
echo ""
echo "📊 Service Status:"
echo "  Backend API:  http://localhost:8000 (PID: ${BACKEND_PID:-Already running})"
echo "  Frontend:     http://localhost:3000 (PID: ${FRONTEND_PID:-Already running})"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
echo ""
echo "📝 Log Files:"
echo "  Backend:      $SCRIPT_DIR/backend.log"
echo "  Celery:       $SCRIPT_DIR/celery.log"
echo "  Frontend:     $SCRIPT_DIR/frontend.log"
echo ""
echo "🔍 Monitoring Commands:"
echo "  Health Check: ./health-check.sh"
echo "  Celery Status: cd backend && source venv/bin/activate && celery -A core.celery_app inspect active"
echo "  Redis Status: redis-cli ping"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running and wait for interrupt
wait
