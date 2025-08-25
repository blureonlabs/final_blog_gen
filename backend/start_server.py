#!/usr/bin/env python3
"""
Blu Blog Gen Backend Server Startup Script
This script starts the FastAPI server with enhanced Swagger documentation
"""

import uvicorn
import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ Python-dotenv is installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install python-dotenv")
        return False
    
    return True

def check_environment():
    """Check if environment variables are set"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("Please create a .env file with your configuration")
        print("You can copy from env.template")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("✅ Environment variables are configured")
    return True

def print_startup_info():
    """Print startup information and available endpoints"""
    print("\n" + "="*60)
    print("🚀 Blu Blog Gen Backend Server")
    print("="*60)
    print()
    print("📚 Available Documentation:")
    print("   • Swagger UI:     http://localhost:8000/docs")
    print("   • ReDoc:          http://localhost:8000/redoc")
    print("   • OpenAPI Schema: http://localhost:8000/openapi.json")
    print()
    print("🔧 API Endpoints:")
    print("   • Health Check:   http://localhost:8000/health")
    print("   • API Status:     http://localhost:8000/")
    print("   • Projects:       http://localhost:8000/api/projects")
    print("   • Content Gen:    http://localhost:8000/api/content-generation")
    print("   • WordPress:      http://localhost:8000/api/wordpress-accounts")
    print("   • API Keys:       http://localhost:8000/api/api-keys")
    print("   • Blogs:          http://localhost:8000/api/blogs")
    print()
    print("🔑 Authentication:")
    print("   • All endpoints require JWT authentication")
    print("   • Use the 'Authorize' button in Swagger UI")
    print("   • Format: Bearer <your-jwt-token>")
    print()
    print("🧪 Testing:")
    print("   • Open http://localhost:8000/docs in your browser")
    print("   • Click 'Authorize' and enter your JWT token")
    print("   • Use 'Try it out' to test any endpoint")
    print()
    print("="*60)
    print("Starting server... Press Ctrl+C to stop")
    print("="*60)

def main():
    """Main startup function"""
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("🔍 Checking environment...")
    if not check_environment():
        print("⚠️  Continuing with default values...")
    
    print_startup_info()
    
    try:
        # Start the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["."],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
