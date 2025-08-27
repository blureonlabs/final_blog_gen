@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 🚀 Blu Blog Gen - Service Startup Script for Windows
REM This script starts all required services for the blog generation system

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo 🚀 Starting Blu Blog Gen Services...
echo Working directory: %SCRIPT_DIR%

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH. Please install Node.js 18+ first.
    pause
    exit /b 1
)

REM Check if Docker is available for Redis
docker --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Docker is not available. Please install Docker Desktop for Windows.
    echo You can download it from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Start Redis using Docker
echo 📡 Starting Redis...
docker run -d -p 6379:6379 --name blureon-redis redis:7-alpine >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Redis container already exists, starting it...
    docker start blureon-redis >nul 2>&1
)

REM Wait for Redis to be ready
echo Waiting for Redis to be ready...
timeout /t 5 /nobreak >nul

REM Test Redis connection
echo Testing Redis connection...
docker exec blureon-redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ❌ Redis failed to start or is not responding
    pause
    exit /b 1
)
echo ✅ Redis is running and responding

REM Start Backend
echo 🔧 Starting Backend API...
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo ⚠️ Virtual environment not found. Creating one...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements if needed
if not exist "requirements_installed" (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    echo. > requirements_installed
)

REM Check if backend is already running
netstat -an | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo ⚠️ Backend is already running on port 8000
) else (
    REM Start backend in new window
    start "Backend API" cmd /k "cd /d %SCRIPT_DIR%backend && call venv\Scripts\activate.bat && python start_server.py"
    echo ✅ Backend started in new window
)

cd ..

REM Wait for backend to be ready
echo Waiting for Backend to be ready...
timeout /t 8 /nobreak >nul

REM Start Celery Worker
echo ⚡ Starting Celery Worker...
cd backend
call venv\Scripts\activate.bat

REM Start Celery worker in new window
start "Celery Worker" cmd /k "cd /d %SCRIPT_DIR%backend && call venv\Scripts\activate.bat && celery -A core.celery_app worker --loglevel=info --queues=wordpress_publishing,content_generation,blog_formatting,image_generation"
echo ✅ Celery worker started in new window

cd ..

REM Wait for Celery to initialize
echo Waiting for Celery to initialize...
timeout /t 5 /nobreak >nul

REM Start Frontend
echo 🎨 Starting Frontend...
cd "%SCRIPT_DIR%"

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install
)

REM Check if frontend is already running
netstat -an | findstr ":3000" >nul 2>&1
if not errorlevel 1 (
    echo ⚠️ Frontend is already running on port 3000
) else (
    REM Start frontend in new window
    start "Frontend" cmd /k "cd /d %SCRIPT_DIR% && npm run dev"
    echo ✅ Frontend started in new window
)

REM Wait for frontend to be ready
echo Waiting for Frontend to be ready...
timeout /t 8 /nobreak >nul

REM Final status
echo.
echo ✅ All services started successfully!
echo.
echo 📊 Service Status:
echo   Backend API:  http://localhost:8000
echo   Frontend:     http://localhost:3000
echo   API Docs:     http://localhost:8000/docs
echo   Health Check: http://localhost:8000/health
echo.
echo 🔍 Monitoring:
echo   - Check each service window for logs and status
echo   - Redis: docker logs blureon-redis
echo   - Backend: Check the Backend API window
echo   - Celery: Check the Celery Worker window
echo   - Frontend: Check the Frontend window
echo.
echo 🛑 To stop services:
echo   - Close each service window
echo   - Stop Redis: docker stop blureon-redis
echo.
echo Press any key to open the frontend in your browser...
pause >nul

REM Open frontend in default browser
start http://localhost:3000

echo.
echo 🌐 Frontend opened in browser
echo.
echo Services are now running in separate windows.
echo Keep this window open to monitor the startup process.
echo.
echo Press any key to exit...
pause >nul
