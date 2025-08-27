# 🚀 Complete Service Running Guide - Blu Blog Gen

This guide provides step-by-step instructions to run your complete blog generation service, including frontend, backend, Celery workers, Redis, and all supporting services.

## 📋 Table of Contents

1. [Prerequisites & System Requirements](#prerequisites--system-requirements)
2. [Environment Setup](#environment-setup)
3. [Service Startup Sequence](#service-startup-sequence)
4. [Individual Service Management](#individual-service-management)
5. [Docker Deployment](#docker-deployment)
6. [Monitoring & Health Checks](#monitoring--health-checks)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

## 🔧 Prerequisites & System Requirements

### System Requirements
- **OS**: macOS, Linux, or Windows (with WSL)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 2GB+ free space
- **Network**: Internet access for API calls

### Required Software
- **Node.js**: Version 18+ (included in `node-local/` folder)
- **Python**: Version 3.8+
- **Redis**: Version 6.0+
- **Git**: For version control

### Required Accounts & API Keys
- **Supabase Account**: Database and authentication
- **OpenAI API Key**: Content generation
- **Google Gemini API Key**: Alternative AI content generation

## 🌍 Environment Setup

### 1. Clone & Setup Project
```bash
# Navigate to your project directory
cd /Users/hari/Downloads/final_blog_gen

# Verify project structure
ls -la
```

### 2. Frontend Environment (.env.local)
Create `.env.local` in the root directory:
```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics
NEXT_PUBLIC_GA_ID=your-ga-id
```

### 3. Backend Environment (.env)
Create `.env` in the `backend/` directory:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# AI API Keys
OPENAI_API_KEY=your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Storage Configuration
STORAGE_BUCKET_NAME=blog-content
STORAGE_REGION=auto

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
ENVIRONMENT=development

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
```

## 🚀 Service Startup Sequence

### Option 1: Manual Startup (Development)
Open **4 terminal windows** and run services in this order:

#### Terminal 1: Start Redis
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Windows (WSL)
sudo service redis-server start

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

#### Terminal 2: Start Backend API
```bash
cd /Users/hari/Downloads/final_blog_gen/backend

# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
python start_server.py
# OR
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 3: Start Celery Worker
```bash
cd /Users/hari/Downloads/final_blog_gen/backend

# Activate virtual environment
source venv/bin/activate

# Start Celery worker with all queues
celery -A core.celery_app worker --loglevel=info --queues=wordpress_publishing,content_generation,blog_formatting,image_generation

# OR start specific queue only
celery -A core.celery_app worker --loglevel=info --queues=content_generation

> **Note**: The system currently uses **4 active queues**: `wordpress_publishing`, `content_generation`, `blog_formatting`, and `image_generation`. While there's a `seo_optimization.py` task file in the codebase, it's not currently being used in the active workflow.
```

#### Terminal 4: Start Frontend
```bash
cd /Users/hari/Downloads/final_blog_gen

# Install dependencies (first time only)
npm install

# Start Next.js development server
npm run dev
```

### Option 2: Automated Startup Script
Create a startup script for convenience:

#### Create `start-services.sh` (macOS/Linux)
```bash
#!/bin/bash
echo "🚀 Starting Blu Blog Gen Services..."

# Start Redis
echo "📡 Starting Redis..."
brew services start redis
sleep 2

# Start Backend
echo "🔧 Starting Backend API..."
cd backend
source venv/bin/activate
python start_server.py &
BACKEND_PID=$!
sleep 3

# Start Celery Worker
echo "⚡ Starting Celery Worker..."
celery -A core.celery_app worker --loglevel=info --queues=wordpress_publishing,content_generation,blog_formatting,image_generation &
CELERY_PID=$!
sleep 2

# Start Frontend
echo "🎨 Starting Frontend..."
cd ..
npm run dev &
FRONTEND_PID=$!

echo "✅ All services started!"
echo "Backend PID: $BACKEND_PID"
echo "Celery PID: $CELERY_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "🌐 Services available at:"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID $CELERY_PID $FRONTEND_PID; brew services stop redis; exit" INT
wait
```

#### Create `start-services.bat` (Windows)
```batch
@echo off
echo 🚀 Starting Blu Blog Gen Services...

REM Start Redis (if using Docker)
echo 📡 Starting Redis...
docker run -d -p 6379:6379 redis:alpine
timeout /t 3

REM Start Backend
echo 🔧 Starting Backend API...
cd backend
call venv\Scripts\activate
start "Backend API" python start_server.py
timeout /t 3

REM Start Celery Worker
echo ⚡ Starting Celery Worker...
start "Celery Worker" celery -A core.celery_app worker --loglevel=info --queues=wordpress_publishing,content_generation,blog_formatting,image_generation
timeout /t 2

REM Start Frontend
echo 🎨 Starting Frontend...
cd ..
start "Frontend" npm run dev

echo ✅ All services started!
echo.
echo 🌐 Services available at:
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
pause
```

## 🐳 Docker Deployment

### Quick Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Individual Docker Services
```bash
# Start Redis only
docker run -d -p 6379:6379 --name blureon-redis redis:7-alpine

# Start Backend
cd backend
docker build -t blu-blog-backend .
docker run -d -p 8000:8000 --name blureon-backend blu-blog-backend

# Start Frontend
docker build -f Dockerfile.frontend -t blu-blog-frontend .
docker run -d -p 3000:3000 --name blureon-frontend blu-blog-frontend
```

## 📊 Monitoring & Health Checks

### Service Status Check
```bash
# Check Redis
redis-cli ping

# Check Backend
curl http://localhost:8000/health

# Check Frontend
curl http://localhost:3000

# Check Celery Worker
celery -A core.celery_app inspect active
```

### Celery Monitoring
```bash
# Check worker status
celery -A core.celery_app inspect stats

# Check active tasks
celery -A core.celery_app inspect active

# Check queue lengths
celery -A core.celery_app inspect stats

# Monitor specific queue
celery -A core.celery_app worker --queues=wordpress_publishing --loglevel=info
```

### Web-based Monitoring
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔍 Troubleshooting

### Common Issues & Solutions

#### 1. Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping

# If not running, start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
sudo service redis-server start  # WSL
```

#### 2. Backend Won't Start
```bash
# Check dependencies
cd backend
pip install -r requirements.txt

# Check environment variables
cat .env

# Check port availability
lsof -i :8000

# Start with verbose logging
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

#### 3. Celery Worker Issues
```bash
# Check Redis connection
redis-cli ping

# Check Celery configuration
python -c "from core.celery_app import celery_app; print(celery_app.conf.broker_url)"

# Start worker with debug logging
celery -A core.celery_app worker --loglevel=debug

# Check task registration
celery -A core.celery_app inspect registered
```

#### 4. Frontend Build Issues
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install

# Check Node.js version
node --version  # Should be 18+

# Use included Node.js
./node-local/node-v20.11.1-win-x64/node.exe --version
```

#### 5. Port Conflicts
```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :6379  # Redis

# Kill conflicting processes
kill -9 <PID>
```

### Log Analysis
```bash
# Backend logs (in terminal)
# Look for error messages and stack traces

# Celery logs (in terminal)
# Look for task failures and connection issues

# Frontend logs (browser console)
# Press F12 and check Console tab
```

## 🚀 Production Deployment

### Environment Variables for Production
```env
# Production .env
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Use production Redis
REDIS_URL=redis://your-redis-server:6379

# Use production Supabase
SUPABASE_URL=https://your-production-project.supabase.co
```

### Production Startup Commands
```bash
# Backend (production)
cd backend
source venv/bin/activate
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Celery (production)
cd backend
source venv/bin/activate
celery -A core.celery_app worker --loglevel=info --concurrency=4 --queues=wordpress_publishing,content_generation,blog_formatting,image_generation

# Frontend (production)
npm run build
npm start
```

### Systemd Service Files (Linux)
```bash
# Create service files for auto-startup
sudo nano /etc/systemd/system/blu-blog-backend.service
sudo nano /etc/systemd/system/blu-blog-celery.service
sudo nano /etc/systemd/system/blu-blog-frontend.service

# Enable and start services
sudo systemctl enable blu-blog-backend
sudo systemctl start blu-blog-backend
```

## 📱 Service Management Commands

### Quick Service Control
```bash
# Start all services
./start-services.sh

# Stop all services
pkill -f "python start_server.py"
pkill -f "celery"
pkill -f "npm run dev"
brew services stop redis

# Restart specific service
# Backend
pkill -f "python start_server.py"
cd backend && source venv/bin/activate && python start_server.py &

# Celery
pkill -f "celery"
cd backend && source venv/bin/activate && celery -A core.celery_app worker --loglevel=info --queues=wordpress_publishing,content_generation,blog_formatting,image_generation &
```

### Health Check Script
```bash
#!/bin/bash
echo "🔍 Health Check - Blu Blog Gen Services"
echo "======================================"

# Check Redis
echo -n "Redis: "
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Backend
echo -n "Backend API: "
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Frontend
echo -n "Frontend: "
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Celery
echo -n "Celery Worker: "
if celery -A core.celery_app inspect active > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

echo "======================================"
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Backend README**: [backend/README.md](./backend/README.md)
- **Swagger Guide**: [backend/SWAGGER_GUIDE.md](./backend/SWAGGER_GUIDE.md)
- **Supabase Setup**: [SUPABASE_SETUP.md](./SUPABASE_SETUP.md)
- **Content Generation**: [CONTENT_GENERATION_SERVICE.md](./CONTENT_GENERATION_SERVICE.md)

## 🆘 Getting Help

### When Things Go Wrong
1. **Check logs** in each terminal window
2. **Verify environment variables** are set correctly
3. **Check service dependencies** (Redis → Backend → Celery → Frontend)
4. **Use health check script** to identify issues
5. **Check browser console** for frontend errors

### Support Channels
- **GitHub Issues**: Create detailed bug reports
- **Team Documentation**: Check internal docs
- **API Testing**: Use Swagger UI at `/docs`
- **Logs**: Check terminal outputs for error messages

---

**Last Updated**: December 2024  
**Maintainer**: Blu Blog Gen Development Team  
**Version**: 1.0.0
