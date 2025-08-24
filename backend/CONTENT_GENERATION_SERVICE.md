# Content Generation Service

The Content Generation Service is the core microservice responsible for generating blog content using AI models (OpenAI and Gemini). It provides both synchronous and asynchronous blog generation capabilities with support for batch processing.

## 🏗️ Architecture

### Components

1. **AI Client** (`core/ai_client.py`)
   - Handles communication with OpenAI and Gemini APIs
   - Supports feature flag selection between AI providers
   - Provides both single and batch blog generation

2. **Content Generation Router** (`routers/content_generation.py`)
   - REST API endpoints for blog generation
   - Project validation and user authentication
   - Progress tracking and status updates

3. **Content Generation Tasks** (`tasks/content_generation.py`)
   - Asynchronous blog generation using background tasks
   - Batch processing for scalability
   - Error handling and retry mechanisms

## 🚀 Features

### AI Model Support
- **OpenAI**: GPT-3.5-turbo, GPT-4, GPT-4-turbo
- **Gemini**: gemini-pro, gemini-pro-vision
- **Feature Flag**: Users can choose which AI model to use via UI

### Blog Generation Capabilities
- Single blog generation
- Batch blog generation (configurable batch sizes)
- Automatic title extraction from content
- Content variation to avoid duplicates
- Progress tracking and logging

### Database Integration
- Stores generated blogs in the `blogs` table
- Tracks generation metadata (AI model, tokens used, batch info)
- Maintains generation logs for debugging
- Updates project status and progress

## 📡 API Endpoints

### Generate Blogs
```http
POST /api/content-generation/generate
```

**Request Body:**
```json
{
  "project_id": "uuid",
  "prompt": "Your blog topic",
  "num_blogs": 10,
  "ai_model": "openai",
  "ai_model_version": "gpt-3.5-turbo",
  "batch_size": 5
}
```

**Response:**
```json
{
  "project_id": "uuid",
  "task_id": "blog_gen_uuid_userid",
  "message": "Blog generation started for 10 blogs",
  "estimated_time": 20,
  "blogs_requested": 10,
  "batch_size": 5
}
```

### Get Project Blogs
```http
GET /api/content-generation/blogs/{project_id}?page=1&per_page=20
```

### Get Single Blog
```http
GET /api/content-generation/blog/{blog_id}
```

### Get Blog Preview
```http
GET /api/content-generation/preview/{blog_id}
```

### Get Generation Status
```http
GET /api/content-generation/generation-status/{project_id}
```

### Get Available Models
```http
GET /api/content-generation/available-models
```

## 🗄️ Database Schema

### Blogs Table
```sql
CREATE TABLE blogs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id),
  title TEXT,
  content TEXT,
  prompt TEXT NOT NULL,
  ai_model TEXT NOT NULL,
  ai_model_version TEXT,
  seo_meta JSONB,
  status TEXT DEFAULT 'draft',
  wordpress_url TEXT,
  wordpress_post_id TEXT,
  error_message TEXT,
  generation_logs JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Generation Metadata
The `seo_meta` field stores:
```json
{
  "generation_model": "openai",
  "model_version": "gpt-3.5-turbo",
  "tokens_used": 1250,
  "batch_number": 1,
  "blog_number": 3,
  "generated_at": 1703123456.789
}
```

### Generation Logs
The `generation_logs` field tracks:
```json
[
  {
    "timestamp": 1703123456.789,
    "message": "Blog generated successfully",
    "status": "success"
  }
]
```

## 🔧 Configuration

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### AI Model Selection
Users can select AI models through the UI:
1. **OpenAI Models**: gpt-4, gpt-4-turbo, gpt-3.5-turbo, gpt-3.5-turbo-16k
2. **Gemini Models**: gemini-pro, gemini-pro-vision

## 📊 Workflow

### Blog Generation Process

1. **User Request**
   - User submits project with prompt and number of blogs
   - System validates project access and AI model availability

2. **Background Task Creation**
   - Blog generation starts as background task
   - Project status updated to "generating"

3. **Batch Processing**
   - Blogs generated in configurable batches (default: 5)
   - Each batch processed sequentially to avoid rate limiting

4. **Content Generation**
   - AI client generates blog content using selected model
   - Title extracted from generated content
   - Content stored in database with metadata

5. **Progress Tracking**
   - Project progress updated after each batch
   - Logs created for monitoring and debugging

6. **Completion**
   - Project status updated to "completed" or "completed_with_errors"
   - Final summary logged

## 🧪 Testing

### Test Script
Run the test script to verify the service:
```bash
cd backend
python test_content_generation.py
```

### Test Coverage
- AI client initialization
- Model availability checking
- Single blog generation
- Multiple blog generation
- Configuration loading

## 🚨 Error Handling

### Common Errors
1. **API Key Missing**: Returns 400 with clear error message
2. **Rate Limiting**: Automatic delays between batches
3. **AI Model Unavailable**: Graceful fallback and error reporting
4. **Database Errors**: Logged and reported to user

### Retry Mechanism
- Failed blogs can be retried individually
- Batch failures don't stop entire process
- Error logs maintained for debugging

## 📈 Performance

### Batch Processing
- Default batch size: 5 blogs
- Configurable via API request
- Automatic delays between batches (2 seconds)

### Rate Limiting
- OpenAI: Respects API rate limits
- Gemini: Built-in rate limiting protection
- Batch delays prevent overwhelming APIs

### Scalability
- Asynchronous processing
- Background task execution
- Progress tracking for large projects

## 🔮 Future Enhancements

### Planned Features
1. **Content Quality Scoring**: AI-powered content evaluation
2. **Template System**: Predefined blog structures
3. **Multi-language Support**: Generate blogs in different languages
4. **Content Optimization**: Automatic content improvement suggestions
5. **Advanced Prompting**: Dynamic prompt generation based on context

### Integration Points
1. **SEO Service**: Content optimization and keyword integration
2. **Image Generation**: Featured image creation
3. **WordPress Publishing**: Direct content publishing
4. **Analytics**: Content performance tracking

## 📚 Usage Examples

### Generate 10 Blogs
```python
import requests

response = requests.post(
    "http://localhost:8000/api/content-generation/generate",
    json={
        "project_id": "your-project-uuid",
        "prompt": "Digital marketing strategies for small businesses",
        "num_blogs": 10,
        "ai_model": "openai",
        "ai_model_version": "gpt-3.5-turbo",
        "batch_size": 5
    }
)

print(response.json())
```

### Monitor Progress
```python
import requests
import time

project_id = "your-project-uuid"

while True:
    response = requests.get(
        f"http://localhost:8000/api/content-generation/generation-status/{project_id}"
    )
    status = response.json()
    
    print(f"Progress: {status['progress_percentage']}%")
    print(f"Blogs generated: {status['blogs_generated']}/{status['total_blogs_requested']}")
    
    if status['project_status'] in ['completed', 'completed_with_errors', 'failed']:
        break
    
    time.sleep(30)  # Check every 30 seconds
```

## 🛠️ Troubleshooting

### Common Issues

1. **AI Models Not Available**
   - Check API keys in environment variables
   - Verify API key validity
   - Check API quota limits

2. **Generation Failures**
   - Review error logs in database
   - Check AI API status
   - Verify prompt quality and length

3. **Performance Issues**
   - Reduce batch size
   - Check API rate limits
   - Monitor database performance

### Debug Mode
Enable debug logging by setting:
```bash
DEBUG=true
```

### Log Analysis
Check the `logs` table for detailed execution information:
```sql
SELECT * FROM logs WHERE project_id = 'your-project-uuid' ORDER BY timestamp DESC;
```
