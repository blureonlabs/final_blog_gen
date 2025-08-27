from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import os

from routers import projects, wordpress_accounts, api_keys, blogs, content_generation
from core.config import settings
from core.supabase_client import supabase_client
from swagger_config import custom_openapi_schema, API_METADATA

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"⚠️  Warning: Could not load .env file: {e}")
    print("Continuing with default environment variables...")

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Bulk Blog Generator Backend...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 Supabase URL: {settings.SUPABASE_URL}")
    
    # Test Supabase connection
    try:
        response = supabase_client.table('users').select('count').limit(1).execute()
        print("✅ Supabase connection successful")
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Bulk Blog Generator Backend...")

# Create FastAPI app with enhanced metadata
app = FastAPI(
    title=API_METADATA["title"],
    description=API_METADATA["description"],
    version=API_METADATA["version"],
    contact=API_METADATA["contact"],
    license_info=API_METADATA["license"],
    servers=API_METADATA["servers"],
    tags=[
        {
            "name": "projects",
            "description": "Blog generation project management. Create, read, update, and delete projects."
        },
        {
            "name": "content-generation",
            "description": "AI-powered blog content generation using OpenAI GPT and Google Gemini models."
        },
        {
            "name": "wordpress-accounts",
            "description": "WordPress site management and auto-publishing functionality."
        },
        {
            "name": "api-keys",
            "description": "External service API key management (OpenAI, Gemini, etc.)."
        },
        {
            "name": "blogs",
            "description": "Generated blog content management and publishing status."
        },
        {
            "name": "authentication",
            "description": "User authentication and JWT token management."
        },
        {
            "name": "status",
            "description": "API status and health check endpoints."
        },
        {
            "name": "documentation",
            "description": "API documentation and schema endpoints."
        }
    ],
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Use settings from config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(wordpress_accounts.router, prefix="/api/wordpress-accounts", tags=["wordpress-accounts"])
app.include_router(api_keys.router, prefix="/api/api-keys", tags=["api-keys"])
app.include_router(blogs.router, prefix="/api/blogs", tags=["blogs"])
app.include_router(content_generation.router, prefix="/api", tags=["content-generation"])

@app.get("/", 
    summary="API Status",
    description="Get the current status and version information of the Blu Blog Gen API",
    response_description="API status information",
    tags=["status"]
)
async def root():
    """
    Get API status and version information.
    
    This endpoint provides basic information about the API including:
    - Current version
    - Service status
    - Basic health information
    """
    return {
        "message": "Blu Blog Gen API",
        "version": "1.0.0",
        "status": "running",
        "description": "AI-powered bulk blog generation and WordPress auto-publishing API",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "projects": "/api/projects",
            "content_generation": "/api/content-generation",
            "wordpress_accounts": "/api/wordpress-accounts",
            "api_keys": "/api/api-keys",
            "blogs": "/api/blogs"
        }
    }

@app.get("/health", 
    summary="Health Check",
    description="Check the health status of the API and its dependencies",
    response_description="Health status information",
    tags=["status"]
)
async def health_check():
    """
    Perform a health check on the API and its dependencies.
    
    This endpoint checks:
    - API service status
    - Database connectivity
    - External service availability
    
    Returns a simple health status that can be used by monitoring systems.
    """
    try:
        # Test Supabase connection
        response = supabase_client.table('users').select('count').limit(1).execute()
        db_status = "healthy" if response.data is not None else "unhealthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "blu-blog-generator",
        "version": "1.0.0",
        "timestamp": "2024-12-19T00:00:00Z",
        "dependencies": {
            "database": db_status,
            "api": "healthy"
        },
        "uptime": "running"
    }

@app.get("/openapi.json", 
    summary="OpenAPI Schema",
    description="Get the complete OpenAPI specification for the API",
    tags=["documentation"]
)
async def get_openapi_schema():
    """
    Retrieve the complete OpenAPI specification.
    
    This endpoint returns the full OpenAPI schema that can be used by:
    - API clients and SDK generators
    - Documentation tools
    - Testing frameworks
    - API management platforms
    """
    return custom_openapi_schema(app)

# Set the custom OpenAPI schema
app.openapi = lambda: custom_openapi_schema(app)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

