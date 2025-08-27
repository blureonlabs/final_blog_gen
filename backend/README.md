# Bulk Blog Generator Backend

FastAPI backend for the AI-powered bulk blog generation and WordPress auto-publishing system.

## 🚀 Features

- **Project Management**: Create, read, update, and delete blog generation projects
- **WordPress Integration**: Manage WordPress site connections
- **API Key Management**: Store and manage external service API keys (OpenAI, Gemini, SERP)
- **User Authentication**: JWT-based authentication with Supabase
- **Real-time Updates**: Supabase realtime subscriptions for live progress updates

## 🏗️ Architecture

- **FastAPI**: Modern, fast web framework for building APIs
- **Supabase**: Database, authentication, and realtime subscriptions
- **Pydantic**: Data validation and serialization
- **JWT**: JSON Web Token authentication

## 📁 Project Structure

```
backend/
├── core/                   # Core configuration and utilities
│   ├── config.py          # Environment variables and settings
│   ├── supabase_client.py # Supabase client configuration
│   └── auth.py            # Authentication utilities
├── models/                 # Pydantic data models
│   ├── project.py         # Project data models
│   ├── wordpress_account.py # WordPress account models
│   └── api_key.py         # API key models
├── routers/                # API route handlers
│   ├── projects.py        # Project management endpoints
│   ├── wordpress_accounts.py # WordPress account endpoints
│   └── api_keys.py        # API key management endpoints
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the backend directory with:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# App Settings
SECRET_KEY=your_secret_key
ENVIRONMENT=development
DEBUG=true

# External APIs (Optional)
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
SERP_API_KEY=your_serp_key
```

### 3. Database Setup

Ensure you have the following tables in your Supabase database:

- `users` (handled by Supabase Auth)
- `projects`
- `wordpress_accounts`
- `api_keys`
- `activity_logs`

### 4. Run the Backend

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Endpoints

### Projects

- `POST /api/projects/create` - Create a new project
- `GET /api/projects` - List user's projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `GET /api/projects/{id}/status` - Get project status

### WordPress Accounts

- `POST /api/wordpress-accounts` - Create WordPress account
- `GET /api/wordpress-accounts` - List user's WordPress accounts
- `GET /api/wordpress-accounts/{id}` - Get account details
- `PUT /api/wordpress-accounts/{id}` - Update account
- `DELETE /api/wordpress-accounts/{id}` - Delete account
- `POST /api/wordpress-accounts/{id}/test` - Test connection

### API Keys

- `POST /api/api-keys` - Create API key
- `GET /api/api-keys` - List user's API keys
- `GET /api/api-keys/services` - Get keys grouped by service
- `GET /api/api-keys/{id}` - Get key details
- `PUT /api/api-keys/{id}` - Update key
- `DELETE /api/api-keys/{id}` - Delete key

## 🔐 Authentication

All endpoints (except health check) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## 🧪 Testing

The API includes automatic OpenAPI documentation. Visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔄 Next Steps

This backend provides the foundation for:

1. **Content Generation Service**: AI-powered blog generation
2. **SEO Optimization Service**: Content optimization and metadata
3. **Image Generation Service**: AI-generated featured images
4. **WordPress Publishing Service**: Automated post publishing
5. **Task Queue**: Background job processing with Celery + Redis

## 📝 Notes

- Passwords and API keys are stored in plain text for development. In production, implement encryption.
- The authentication system is designed to work with Supabase Auth JWT tokens.
- All database operations use Supabase's Python client for consistency.

## Multi-Threading Blog Generation

The system now supports **automatic multi-threading** for significantly improved performance when generating multiple blogs:

### Key Benefits
- **Automatic optimization** - no user configuration required
- **2-4x faster generation** for multiple blogs
- **Concurrent processing** instead of sequential waiting
- **Configurable concurrency levels** (1-10 concurrent blogs)
- **Smart detection** - single blog uses sequential, multiple blogs use multi-threading

### How It Works
- **1 blog**: Automatically uses sequential generation
- **2+ blogs**: Automatically uses multi-threading for faster processing
- **No user selection needed** - the system chooses the best approach

### Usage
```python
# Single blog - automatically sequential
blogs = await blog_generation_service.generate_blogs_for_project(
    project_id="your_project",
    num_blogs=1  # Uses sequential mode
)

# Multiple blogs - automatically multi-threaded
blogs = await blog_generation_service.generate_blogs_for_project(
    project_id="your_project",
    num_blogs=10,  # Automatically uses multi-threading
    max_concurrent_blogs=5  # Optional: control concurrency
)
```

### API Endpoints
- `POST /content-generation/generate-direct` - Automatic method selection based on blog count

See [MULTITHREADING_IMPLEMENTATION.md](MULTITHREADING_IMPLEMENTATION.md) for detailed documentation.
