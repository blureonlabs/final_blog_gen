# 🚀 Swagger API Documentation Guide

## 📖 Overview

Your Blu Blog Gen backend now includes comprehensive Swagger/OpenAPI documentation that allows you to:

- **View all API endpoints** with detailed descriptions
- **Test API calls directly** from the browser
- **See request/response schemas** and examples
- **Authenticate and authorize** requests
- **Generate client code** for various programming languages

## 🌐 Accessing Swagger Documentation

### 1. Start Your Backend Server

```bash
cd backend
python start_server.py
```

Or manually:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Open Swagger UI

Navigate to: **http://localhost:8000/docs**

You'll see the interactive Swagger documentation interface.

## 🔑 Authentication Setup

### Step 1: Get Your JWT Token

You need a valid JWT token to test the API endpoints. This token should come from your authentication service (Supabase Auth).

### Step 2: Authorize in Swagger

1. **Click the "Authorize" button** at the top of the Swagger UI
2. **Enter your token** in the format: `Bearer <your-jwt-token>`
3. **Click "Authorize"** to save your token
4. **Close the authorization dialog**

Now all your API calls will automatically include the authentication header.

## 🧪 Testing Endpoints

### Basic Testing Flow

1. **Find an endpoint** you want to test
2. **Click "Try it out"** button
3. **Fill in the parameters** (use examples or your own data)
4. **Click "Execute"** to make the API call
5. **View the response** including status code, headers, and body

### Example: Creating a Project

1. **Navigate to** `/api/projects/create` (POST)
2. **Click "Try it out"**
3. **Fill in the request body**:
   ```json
   {
     "name": "My First Blog Project",
     "description": "A test project for learning",
     "num_blogs": 5,
     "ai_model": "gpt-4",
     "wordpress_account_id": null,
     "api_keys": {
       "openai": "sk-your-openai-key-here"
     }
   }
   ```
4. **Click "Execute"**
5. **View the response** - you should see a 201 Created with project details

## 📚 Available Endpoint Categories

### 📁 Projects
- **Create Project** (`POST /api/projects/create`)
- **List Projects** (`GET /api/projects`)
- **Get Project** (`GET /api/projects/{id}`)
- **Update Project** (`PUT /api/projects/{id}`)
- **Delete Project** (`DELETE /api/projects/{id}`)

### 🤖 Content Generation
- **Generate Blogs** (`POST /api/content-generation/generate`)
- **Generate Direct** (`POST /api/content-generation/generate-direct`)
- **Get Progress** (`GET /api/content-generation/progress/{project_id}`)
- **Cancel Generation** (`POST /api/content-generation/cancel/{project_id}`)

### 🌐 WordPress Integration
- **Add WordPress Site** (`POST /api/wordpress-accounts`)
- **List Sites** (`GET /api/wordpress-accounts`)
- **Get Site** (`GET /api/wordpress-accounts/{id}`)
- **Update Site** (`PUT /api/wordpress-accounts/{id}`)
- **Delete Site** (`DELETE /api/wordpress-accounts/{id}`)
- **Test Connection** (`POST /api/wordpress-accounts/{id}/test`)

### 🔑 API Key Management
- **Store API Key** (`POST /api/api-keys`)
- **List Keys** (`GET /api/api-keys`)
- **Get Key** (`GET /api/api-keys/{id}`)
- **Update Key** (`PUT /api/api-keys/{id}`)
- **Delete Key** (`DELETE /api/api-keys/{id}`)

### 📊 Blog Management
- **List Blogs** (`GET /api/blogs`)
- **Get Blog** (`GET /api/blogs/{id}`)
- **Update Blog** (`PUT /api/blogs/{id}`)
- **Delete Blog** (`DELETE /api/blogs/{id}`)

### 📊 Status & Health
- **API Status** (`GET /`)
- **Health Check** (`GET /health`)
- **OpenAPI Schema** (`GET /openapi.json`)

## 🔧 Advanced Testing Features

### Request/Response Logging

The Swagger UI includes custom interceptors that:
- **Log all requests** to the browser console
- **Add timestamps** to requests for debugging
- **Show response details** in the console

### Custom Examples

Many endpoints include **pre-filled examples** that you can use directly:
- **Project creation** examples
- **Blog generation** request examples
- **WordPress account** configuration examples

### Response Schemas

Each endpoint shows:
- **Expected response format**
- **Data types and validation**
- **Example responses**
- **Error response formats**

## 🚨 Common Testing Scenarios

### 1. Complete Project Workflow

```bash
# 1. Create a project
POST /api/projects/create

# 2. Add API keys
POST /api/api-keys

# 3. Add WordPress site
POST /api/wordpress-accounts

# 4. Generate content
POST /api/content-generation/generate

# 5. Check progress
GET /api/content-generation/progress/{project_id}

# 6. View generated blogs
GET /api/blogs
```

### 2. Error Testing

Test various error conditions:
- **Invalid authentication** (remove token)
- **Missing required fields** (empty request body)
- **Invalid data types** (string instead of number)
- **Non-existent resources** (invalid IDs)

### 3. Performance Testing

- **Large batch requests** (generate 50+ blogs)
- **Concurrent requests** (multiple tabs/windows)
- **Long-running operations** (monitor progress)

## 📱 Alternative Documentation Views

### ReDoc
- **URL**: http://localhost:8000/redoc
- **Features**: Clean, responsive documentation
- **Best for**: Reading and understanding the API

### OpenAPI Schema
- **URL**: http://localhost:8000/openapi.json
- **Features**: Raw OpenAPI specification
- **Best for**: Code generation and integration

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Not authenticated" errors
- **Solution**: Click "Authorize" and enter your JWT token
- **Format**: `Bearer <your-token>`

#### 2. "Validation error" responses
- **Solution**: Check the request body format
- **Tip**: Use the provided examples as templates

#### 3. "Internal server error"
- **Solution**: Check backend logs for detailed error information
- **Common causes**: Database connection issues, missing environment variables

#### 4. CORS errors
- **Solution**: Ensure your frontend is running on localhost:3000
- **Backend CORS**: Configured for localhost:3000 and 127.0.0.1:3000

### Debugging Tips

1. **Check browser console** for request/response logs
2. **Monitor backend terminal** for server logs
3. **Use the health endpoint** to verify service status
4. **Test with simple endpoints** first (like `/health`)

## 🚀 Next Steps

### 1. Generate Client Code

Use the OpenAPI schema to generate client libraries:
- **Python**: `openapi-generator-cli generate -i openapi.json -g python`
- **JavaScript**: `openapi-generator-cli generate -i openapi.json -g javascript`
- **Java**: `openapi-generator-cli generate -i openapi.json -g java`

### 2. Integration Testing

- **Postman**: Import the OpenAPI schema
- **Insomnia**: Use the schema for API testing
- **Custom scripts**: Build automated testing suites

### 3. API Monitoring

- **Health checks**: Monitor `/health` endpoint
- **Performance metrics**: Track response times
- **Error tracking**: Monitor error rates and types

## 📞 Support

If you encounter issues:

1. **Check the backend logs** for detailed error messages
2. **Verify environment variables** are properly set
3. **Test with simple endpoints** first
4. **Check the health endpoint** for service status
5. **Review the OpenAPI schema** for endpoint details

---

**Happy API Testing! 🎉**

Your Swagger documentation is now ready to help you explore and test all the Blu Blog Gen API endpoints!
