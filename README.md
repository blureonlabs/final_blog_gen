# Blu Blog Gen - AI-Powered Bulk Blog Generator

A modern, full-stack application for AI-powered bulk blog generation and WordPress auto-publishing, built with Next.js frontend and FastAPI backend.

## 🚀 Project Overview

Blu Blog Gen is an AI-powered platform that helps users:
- Generate high-quality blog content using AI (OpenAI, Gemini)
- Manage multiple blog generation projects
- Automatically publish content to WordPress sites
- Optimize content for SEO
- Generate AI-powered featured images
- Collaborate with team members on content projects

## 🏗️ Architecture

- **Frontend**: Next.js 14 + React 18 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python + Celery + Redis
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth with JWT
- **Storage**: Supabase Storage + S3
- **AI Services**: OpenAI GPT, Google Gemini
- **Task Queue**: Celery with Redis for background processing

## 📁 Project Structure

```
final_blog_gen/
├── app/                    # Next.js frontend app
├── components/             # React components
├── lib/                    # Frontend utilities
├── backend/                # FastAPI backend
│   ├── core/              # Core configuration
│   ├── models/            # Data models
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   └── tasks/             # Celery background tasks
├── public/                 # Static assets
└── styles/                 # Global styles
```

## 🛠️ Setup Instructions

### Prerequisites

- **Node.js**: Version 18+ (included in `node-local/` folder)
- **Python**: Version 3.8+
- **Redis**: For Celery task queue
- **Supabase Account**: For database and authentication

### 1. Frontend Setup

#### Install Dependencies
```bash
cd final_blog_gen
npm install
# or
pnpm install
```

#### Environment Configuration
Create `.env.local` file in the root directory:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

#### Run Frontend
```bash
# Development mode
npm run dev
# or
pnpm dev

# Build for production
npm run build
npm start
```

Frontend will be available at: `http://localhost:3000`

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Environment Configuration
Create `.env` file in the `backend/` directory:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# AI API Keys
OPENAI_API_KEY=your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# Storage Configuration
STORAGE_BUCKET_NAME=blog-content
STORAGE_REGION=auto

# Database Configuration
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

#### Run Backend
```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using the startup script
python start_server.py

# Or using the main.py file
python main.py
```

Backend will be available at: `http://localhost:8000`

#### Run Celery Worker (for background tasks)
```bash
# Start Celery worker
celery -A core.celery_app worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A core.celery_app beat --loglevel=info
```

### 3. Redis Setup

Install and start Redis:
```bash
# Windows (using WSL or Docker)
# Option 1: Docker
docker run -d -p 6379:6379 redis:alpine

# Option 2: WSL with Ubuntu
sudo apt-get install redis-server
sudo service redis-server start

# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

## 🔑 API Keys & Services

### Required API Keys

#### 1. Supabase
- **SUPABASE_URL**: Your Supabase project URL
- **SUPABASE_ANON_KEY**: Public anonymous key for client-side operations
- **SUPABASE_SERVICE_ROLE_KEY**: Service role key for admin operations

#### 2. AI Services
- **OPENAI_API_KEY**: OpenAI API key for GPT-powered content generation
- **GEMINI_API_KEY**: Google Gemini API key for alternative AI content generation

### Optional API Keys
- **SERP_API_KEY**: For SEO research and keyword analysis
- **WORDPRESS_CREDENTIALS**: Stored per account in the database

### What Each Service Does

#### OpenAI (GPT)
- **Content Generation**: Creates blog posts, articles, and marketing copy
- **Content Optimization**: Improves readability and engagement
- **SEO Enhancement**: Generates meta descriptions and titles

#### Google Gemini
- **Alternative AI**: Backup content generation when OpenAI is unavailable
- **Multimodal Content**: Handles text and image-based content creation
- **Cost Optimization**: Often more cost-effective for certain content types

#### Supabase
- **Database**: Stores projects, blogs, user data, and API keys
- **Authentication**: User login, registration, and session management
- **Storage**: File uploads, blog images, and generated content
- **Real-time Updates**: Live progress tracking for content generation

## 📚 API Documentation & Testing

### Swagger UI (Interactive API Testing)

Your backend includes comprehensive Swagger documentation for testing all API endpoints:

- **URL**: `http://localhost:8000/docs`
- **Features**: Interactive API testing, request/response examples, authentication
- **Best for**: Testing endpoints, understanding API structure, debugging

### Alternative Documentation Views

- **ReDoc**: `http://localhost:8000/redoc` - Clean, responsive documentation
- **OpenAPI Schema**: `http://localhost:8000/openapi.json` - Raw specification for code generation

### Quick Start with Swagger

1. **Start your backend**: `python start_server.py`
2. **Open Swagger UI**: Navigate to `http://localhost:8000/docs`
3. **Authorize**: Click "Authorize" and enter your JWT token
4. **Test endpoints**: Use "Try it out" to test any API endpoint

### Available API Endpoints

- **Projects**: Create, manage, and track blog generation projects
- **Content Generation**: AI-powered blog generation with progress tracking
- **WordPress Integration**: Site management and auto-publishing
- **API Key Management**: Secure storage of external service keys
- **Blog Management**: View and manage generated content

For detailed API testing instructions, see: [SWAGGER_GUIDE.md](./backend/SWAGGER_GUIDE.md)

## 🚀 Running the Complete System

### 1. Start All Services
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Backend
cd backend
python start_server.py

# Terminal 3: Start Celery Worker
cd backend
celery -A core.celery_app worker --loglevel=info

# Terminal 4: Start Frontend
cd final_blog_gen
npm run dev
```

### 2. Verify Setup
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

## 📚 API Endpoints

### Core Endpoints
- `GET /` - API status and version
- `GET /health` - Health check endpoint

### Project Management
- `POST /api/projects/create` - Create new blog generation project
- `GET /api/projects` - List user's projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Content Generation
- `POST /api/content-generation/generate` - Generate blog content using AI
- `POST /api/content-generation/optimize-seo` - Optimize content for SEO
- `POST /api/content-generation/generate-images` - Generate AI-powered featured images

### WordPress Integration
- `POST /api/wordpress-accounts` - Add WordPress site
- `POST /api/publish` - Publish content to WordPress
- `GET /api/wordpress-accounts` - List connected sites

## 🔧 Development Commands

### Frontend
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Backend
```bash
python start_server.py                    # Start with enhanced startup script
uvicorn main:app --reload                # Start with auto-reload
python -m pytest                         # Run tests
celery -A core.celery_app worker --loglevel=info  # Start worker
```

## 🐳 Docker Support

### Backend Docker
```bash
cd backend
docker build -t blu-blog-backend .
docker run -p 8000:8000 blu-blog-backend
```

### Frontend Docker
```bash
cd final_blog_gen
docker build -f Dockerfile.frontend -t blu-blog-frontend .
docker run -p 3000:3000 blu-blog-frontend
```

### Complete Stack with Docker Compose
```bash
docker-compose up -d
```

## 🧪 Testing

### Frontend Tests
```bash
npm run test
npm run test:watch
```

### Backend Tests
```bash
cd backend
python -m pytest
```

### API Testing
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🚨 Troubleshooting

### Common Issues

#### Frontend Won't Start
- Check Node.js version (18+ required)
- Verify `.env.local` configuration
- Clear `node_modules` and reinstall

#### Backend Connection Issues
- Verify Supabase credentials
- Check Redis is running
- Ensure all environment variables are set

#### Celery Worker Issues
- Verify Redis connection
- Check Celery configuration in `core/celery_app.py`
- Ensure all dependencies are installed

#### Swagger Documentation Issues
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify CORS configuration

### Logs
- **Frontend**: Check browser console and terminal
- **Backend**: Check terminal output and logs
- **Celery**: Check worker terminal output

## 📖 Additional Documentation

- [Backend README](./backend/README.md) - Detailed backend setup
- [Swagger Guide](./backend/SWAGGER_GUIDE.md) - API testing guide
- [Supabase Setup](./SUPABASE_SETUP.md) - Database configuration
- [Content Generation Service](./CONTENT_GENERATION_SERVICE.md) - AI service details
- [Team Setup](./TEAM_SETUP.md) - Development workflow

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- **Issues**: Create GitHub issues for bugs/features
- **Documentation**: Check the docs folder and README files
- **API Testing**: Use the Swagger UI at `/docs`
- **Team**: Contact the development team for internal support

---

**Team**: Blu Blog Gen Development Team  
**Maintainer**: @blureonlabs  
**Last Updated**: December 2024
