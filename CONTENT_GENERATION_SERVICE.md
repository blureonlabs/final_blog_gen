# 🚀 Content Generation Service

## Overview

The **Content Generation Service** is the core microservice of the Bulk Blog Generator that handles AI-powered blog creation, SEO optimization, formatting, and WordPress publishing. This service orchestrates the entire workflow from prompt to published blog.

## 🏗️ Architecture

### Service Components

1. **AI Client** (`core/ai_client.py`)
   - Switches between OpenAI and Gemini APIs
   - Feature flag support for model selection
   - Handles content generation and refinement

2. **Celery Tasks** (`tasks/`)
   - `content_generation.py` - Main blog generation workflow
   - `seo_optimization.py` - SEO metadata and optimization
   - `blog_formatting.py` - Content structure and formatting
   - `image_generation.py` - Featured image generation
   - `wordpress_publishing.py` - WordPress integration

3. **Blog Management** (`routers/blogs.py`)
   - REST API endpoints for blog operations
   - Blog generation, preview, and publishing

## 🔄 Workflow

### 1. Blog Generation Request
```
User → Frontend → /api/blogs/generate → Celery Task
```

### 2. Content Generation Pipeline
```
Prompt → AI Generation → SEO Optimization → Formatting → Image Generation → Ready
```

### 3. Publishing Pipeline
```
Ready Blog → WordPress Publishing → Published
```

## 🚀 Getting Started

### Prerequisites

1. **Environment Variables**
   ```bash
   # AI API Keys
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key
   
   # Redis
   REDIS_URL=redis://localhost:6379
   
   # Supabase
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

2. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Service

#### Option 1: Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up backend worker redis
```

#### Option 2: Local Development
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A core.celery_app worker --loglevel=info

# Terminal 3: Start FastAPI Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Blog Generation
```http
POST /api/blogs/generate
Content-Type: application/json

{
  "project_id": "uuid",
  "prompt": "Write about AI in business",
  "num_blogs": 10,
  "ai_model": "openai",
  "batch_size": 5
}
```

### Get Project Blogs
```http
GET /api/blogs/project/{project_id}?page=1&per_page=10&status=ready
```

### Blog Preview
```http
GET /api/blogs/{blog_id}/preview
```

### Publish to WordPress
```http
POST /api/blogs/{blog_id}/publish
Content-Type: application/json

{
  "wordpress_account_id": "uuid",
  "publish_status": "draft",
  "categories": ["Technology", "AI"],
  "tags": ["artificial-intelligence", "business"]
}
```

## 🔧 Configuration

### AI Model Selection

The service supports both OpenAI and Gemini APIs with automatic fallback:

```python
# In your project creation
{
  "ai_model": "openai",  # or "gemini"
  "ai_model_version": "gpt-4"  # or "gemini-pro"
}
```

### Batch Processing

Configure batch sizes for optimal performance:

```python
{
  "batch_size": 5,  # Process 5 blogs simultaneously
  "num_blogs": 100  # Total blogs to generate
}
```

### Task Queues

Tasks are routed to specific queues for better resource management:

- `content_generation` - Blog creation
- `seo_optimization` - SEO processing
- `blog_formatting` - Content structuring
- `image_generation` - Image creation
- `wordpress_publishing` - WordPress integration

## 📊 Monitoring & Logging

### Task Status

Monitor task progress through Supabase:

```sql
-- Check blog generation status
SELECT status, COUNT(*) as count 
FROM blogs 
WHERE project_id = 'your_project_id' 
GROUP BY status;

-- View generation logs
SELECT generation_logs 
FROM blogs 
WHERE id = 'blog_id';
```

### Celery Monitoring

```bash
# Check worker status
celery -A core.celery_app inspect active

# Monitor task progress
celery -A core.celery_app inspect stats

# View task results
celery -A core.celery_app inspect reserved
```

## 🚨 Error Handling

### Common Issues

1. **AI API Rate Limits**
   - Automatic retry with exponential backoff
   - Fallback to alternative model if available

2. **WordPress Connection Issues**
   - Credential validation
   - Network timeout handling
   - Detailed error logging

3. **Content Generation Failures**
   - Partial content recovery
   - Manual review and regeneration options

### Error Recovery

```python
# Check failed blogs
SELECT * FROM blogs WHERE status = 'failed';

# Retry failed generation
# The system automatically retries failed tasks
# Manual retry available through API
```

## 🔒 Security

### Authentication
- JWT-based authentication via Supabase
- User-specific project and blog access
- API key management for external services

### Data Privacy
- User data isolation
- Secure API key storage
- Audit logging for all operations

## 📈 Performance Optimization

### Scaling Strategies

1. **Horizontal Scaling**
   - Multiple Celery workers
   - Load balancing across instances

2. **Batch Processing**
   - Configurable batch sizes
   - Parallel blog generation

3. **Caching**
   - Redis for task results
   - Supabase for data persistence

### Performance Metrics

- **Generation Speed**: ~5 blogs per minute
- **Concurrent Processing**: Up to 20 blogs simultaneously
- **API Response Time**: <200ms for metadata operations

## 🧪 Testing

### Unit Tests
```bash
# Run tests
pytest tests/

# Test specific module
pytest tests/test_content_generation.py
```

### Integration Tests
```bash
# Test with real APIs (requires API keys)
pytest tests/integration/ --env-file=.env.test
```

### Load Testing
```bash
# Test blog generation performance
python scripts/load_test.py --blogs=100 --concurrent=10
```

## 🔄 Deployment

### Production Setup

1. **Environment Configuration**
   ```bash
   # Production environment
   export ENVIRONMENT=production
   export REDIS_URL=redis://your-redis-host:6379
   export SUPABASE_URL=your-production-supabase
   ```

2. **Service Management**
   ```bash
   # Start services
   docker-compose -f docker-compose.yml up -d
   
   # Monitor logs
   docker-compose logs -f backend worker
   ```

3. **Health Checks**
   ```bash
   # Backend health
   curl http://localhost:8000/health
   
   # Worker health
   docker exec blureon-worker celery -A core.celery_app inspect ping
   ```

## 📚 API Documentation

### Interactive Docs
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### SDK Examples

```python
import requests

# Generate blogs
response = requests.post(
    "http://localhost:8000/api/blogs/generate",
    json={
        "project_id": "your_project_id",
        "prompt": "Write about digital marketing",
        "num_blogs": 5,
        "ai_model": "openai"
    },
    headers={"Authorization": "Bearer your_jwt_token"}
)

# Check status
blogs = requests.get(
    f"http://localhost:8000/api/blogs/project/{project_id}",
    headers={"Authorization": "Bearer your_jwt_token"}
)
```

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Create feature branch**
3. **Implement changes**
4. **Add tests**
5. **Submit pull request**

### Code Standards

- **Python**: PEP 8, type hints
- **Testing**: pytest, 90%+ coverage
- **Documentation**: Google-style docstrings

## 📞 Support

### Getting Help

1. **Documentation**: Check this README first
2. **Issues**: GitHub Issues for bugs and features
3. **Discussions**: GitHub Discussions for questions
4. **Email**: support@blureon.com

### Troubleshooting

Common issues and solutions are documented in the [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) file.

---

**Next Steps**: After setting up the Content Generation Service, you can:
1. Test blog generation with sample prompts
2. Configure WordPress accounts for publishing
3. Set up monitoring and alerting
4. Scale the service based on your needs

For more information, see the [main project README](./README.md).
