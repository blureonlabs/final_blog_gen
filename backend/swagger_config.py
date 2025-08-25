"""
Swagger/OpenAPI Configuration for Blu Blog Gen API
This file contains custom configurations and examples for the API documentation
"""

from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

def custom_openapi_schema(app) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced documentation
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers
    )
    
    # Add custom security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from authentication endpoint"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add custom examples
    openapi_schema["components"]["examples"] = {
        "ProjectCreate": {
            "summary": "Sample Project Creation",
            "description": "Example of creating a new blog generation project",
            "value": {
                "name": "My Tech Blog Series",
                "description": "A series of 10 blog posts about modern web development",
                "num_blogs": 10,
                "ai_model": "gpt-4",
                "wordpress_account_id": "550e8400-e29b-41d4-a716-446655440000",
                "api_keys": {
                    "openai": "sk-...",
                    "gemini": "AIza..."
                }
            }
        },
        "ProjectResponse": {
            "summary": "Sample Project Response",
            "description": "Example of a created project response",
            "value": {
                "idx": 0,
                "id": "255fd777-e9dd-4244-a358-aec045f69453",
                "user_id": "00000000-0000-0000-0000-000000000000",
                "name": "Test Project",
                "description": "Test Description",
                "num_blogs": 5,
                "completed_blogs": 0,
                "status": "ready",
                "wordpress_account_id": None,
                "api_keys": None,
                "settings": None,
                "draft_creation_model": "gpt-4",
                "content_vetting_model": "gpt-4",
                "model_settings": None,
                "workflow_preferences": None,
                "created_at": "2025-08-24 20:06:00.75534+00",
                "updated_at": "2025-08-24 20:06:00.75534+00"
            }
        },
        "BlogGenerationRequest": {
            "summary": "Sample Blog Generation Request",
            "description": "Example of requesting blog generation",
            "value": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "prompt": "Write a comprehensive guide about React hooks with practical examples",
                "num_blogs": 5,
                "ai_model": "gpt-4",
                "ai_model_version": "latest",
                "batch_size": 2
            }
        },
        "WordPressAccount": {
            "summary": "Sample WordPress Account",
            "description": "Example of WordPress site configuration",
            "value": {
                "site_name": "My Tech Blog",
                "site_url": "https://mytechblog.com",
                "username": "admin",
                "password": "secure_password_123",
                "api_endpoint": "https://mytechblog.com/wp-json/wp/v2"
            }
        }
    }
    
    # Add custom responses
    openapi_schema["components"]["responses"] = {
        "UnauthorizedError": {
            "description": "Authentication information is missing or invalid",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Not authenticated"
                            }
                        }
                    }
                }
            }
        },
        "ValidationError": {
            "description": "Request validation failed",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "loc": {"type": "array"},
                                        "msg": {"type": "string"},
                                        "type": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "ServerError": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Internal server error occurred"
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Add custom schemas
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "description": "Error message"
            },
            "error_code": {
                "type": "string",
                "description": "Error code for client handling"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "When the error occurred"
            }
        }
    }
    
    # Add operation IDs for better client generation
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                operation = openapi_schema["paths"][path][method]
                if "tags" in operation and "summary" in operation:
                    # Generate operation ID from tag and summary
                    tag = operation["tags"][0] if operation["tags"] else "default"
                    summary = operation["summary"].lower().replace(" ", "_")
                    operation["operationId"] = f"{tag}_{summary}"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Swagger UI custom configuration
SWAGGER_UI_CONFIG = {
    "swagger_ui_parameters": {
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "defaultModelRendering": "example",
        "displayRequestDuration": True,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True,
        "requestInterceptor": """
        function(request) {
            // Add timestamp to requests for debugging
            request.headers['X-Request-Timestamp'] = new Date().toISOString();
            return request;
        }
        """,
        "responseInterceptor": """
        function(response) {
            // Log response for debugging
            console.log('Response:', response);
            return response;
        }
        """
    }
}

# API Documentation metadata
API_METADATA = {
    "title": "Blu Blog Gen API",
    "version": "1.0.0",
    "description": """
    # 🚀 Blu Blog Gen - AI-Powered Bulk Blog Generator API
    
    ## 🔑 Quick Authentication Setup
    
    To use this API, you need to authenticate with a JWT token:
    
    1. **Get your token** from your authentication service
    2. **Click the 'Authorize' button** at the top of this page
    3. **Enter your token** in the format: `Bearer <your-jwt-token>`
    4. **Click 'Authorize'** to save your token
    
    ## 🧪 Testing Endpoints
    
    - **Try it out**: Click the 'Try it out' button on any endpoint
    - **Fill in parameters**: Use the example values or your own data
    - **Execute**: Click 'Execute' to make the actual API call
    - **View response**: See the response, status code, and headers
    
    ## 📚 Available Endpoints
    
    ### 📁 Projects
    - **Create Project**: Start a new blog generation project
    - **List Projects**: Get all your projects with pagination
    - **Get Project**: Retrieve specific project details
    - **Update Project**: Modify existing project settings
    - **Delete Project**: Remove a project and its data
    
    ### 🤖 Content Generation
    - **Generate Blogs**: Start AI-powered blog generation
    - **Generate Direct**: Immediate blog generation (synchronous)
    - **Get Progress**: Check generation status and progress
    - **Cancel Generation**: Stop ongoing generation process
    
    ### 🌐 WordPress Integration
    - **Add Site**: Connect a new WordPress site
    - **List Sites**: View all connected WordPress sites
    - **Test Connection**: Verify site connectivity
    - **Publish Content**: Auto-publish generated blogs
    
    ### 🔑 API Key Management
    - **Store Keys**: Securely store external service API keys
    - **List Keys**: View all your stored API keys
    - **Update Keys**: Modify existing API key configurations
    - **Delete Keys**: Remove stored API keys
    
    ### 📊 Blog Management
    - **List Blogs**: View all generated blog content
    - **Get Blog**: Retrieve specific blog details
    - **Update Blog**: Modify blog content before publishing
    - **Delete Blog**: Remove blog content
    
    ## 🚨 Common HTTP Status Codes
    
    - **200 OK**: Request successful
    - **201 Created**: Resource created successfully
    - **400 Bad Request**: Invalid request data
    - **401 Unauthorized**: Authentication required
    - **403 Forbidden**: Access denied
    - **404 Not Found**: Resource not found
    - **422 Validation Error**: Request validation failed
    - **500 Internal Server Error**: Server error
    
    ## 🔧 Tips for Testing
    
    1. **Start with simple endpoints** like `/health` or `/`
    2. **Use the examples** provided in the request schemas
    3. **Check the response schemas** to understand the data structure
    4. **Use the 'Models' section** to see all data structures
    5. **Monitor the console** for request/response logging
    
    ## 📖 Additional Resources
    
    - **ReDoc Documentation**: Alternative documentation view
    - **OpenAPI Schema**: Raw OpenAPI specification
    - **GitHub Repository**: Source code and issues
    - **Support**: Contact the development team
    
    ---
    
    **Happy API Testing! 🎉**
    """,
    "contact": {
        "name": "Blu Blog Gen Team",
        "email": "support@blubloggen.com",
        "url": "https://github.com/blureonlabs/blu-blog-gen"
    },
    "license": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    "servers": [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.blubloggen.com",
            "description": "Production server"
        }
    ]
}
