# 🚀 Quick Start - Blu Blog Gen

## ⚡ One-Command Startup

### macOS/Linux
```bash
./start-services.sh
```

### Windows
```batch
start-services.bat
```

## 🔍 Health Check
```bash
./health-check.sh
```

## 📋 Manual Startup (4 Terminals)

### Terminal 1: Redis
```bash
brew services start redis  # macOS
sudo systemctl start redis  # Linux
sudo service redis-server start  # WSL
```

### Terminal 2: Backend
```bash
cd backend
source venv/bin/activate
python start_server.py
```

### Terminal 3: Celery Worker
```bash
cd backend
source venv/bin/activate
celery -A core.celery_app worker --loglevel=info --queues=wordpress_publishing,content_generation,blog_formatting,image_generation
```

### Terminal 4: Frontend
```bash
npm install  # First time only
npm run dev
```

## 🌐 Service URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🐳 Docker Quick Start
```bash
docker-compose up -d
```

## 🛑 Stop All Services
```bash
# macOS/Linux
pkill -f "python start_server.py"
pkill -f "celery"
pkill -f "npm run dev"
brew services stop redis

# Windows
# Close each service window manually
docker stop blureon-redis
```

## 🔧 Troubleshooting
```bash
# Check Redis
redis-cli ping

# Check Backend
curl http://localhost:8000/health

# Check Celery
cd backend && source venv/bin/activate && celery -A core.celery_app inspect active

# Health Check
./health-check.sh
```

## 📚 Full Documentation
- **Complete Guide**: [SERVICE_RUNNING_GUIDE.md](./SERVICE_RUNNING_GUIDE.md)
- **Backend README**: [backend/README.md](./backend/README.md)
- **API Testing**: [backend/SWAGGER_GUIDE.md](./backend/SWAGGER_GUIDE.md)
