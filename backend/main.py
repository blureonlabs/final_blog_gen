from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import os

from routers import projects, wordpress_accounts, api_keys, blogs, content_generation
from core.config import settings
from core.supabase_client import supabase_client

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

# Create FastAPI app
app = FastAPI(
    title="Bulk Blog Generator API",
    description="AI-powered bulk blog generation and WordPress auto-publishing API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Your React frontend
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

@app.get("/")
async def root():
    return {
        "message": "Bulk Blog Generator API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "bulk-blog-generator"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
