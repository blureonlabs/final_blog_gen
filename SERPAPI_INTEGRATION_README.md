# SerpAPI Integration for Blog Generation

This document explains how to use the new SerpAPI integration that enhances blog generation with web research capabilities.

## 🚀 Overview

The SerpAPI integration allows your blog generation system to:
1. **Research topics** using Google search results before generating content
2. **Enhance AI prompts** with real-time web data and insights
3. **Include external references** and citations in generated blogs
4. **Improve content quality** with current, relevant information

## 🔧 Setup

### 1. Database Migration

First, run the database migration to add the new SerpAPI columns:

```sql
-- Run this in your Supabase SQL editor
-- File: SUPABASE_SERPAPI_MIGRATION.sql

ALTER TABLE projects ADD COLUMN IF NOT EXISTS serp_api_on BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS serp_api_contents JSONB;
```

### 2. Install Dependencies

The backend now requires additional dependencies:

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `aiohttp>=3.8.0` - For async HTTP requests to SerpAPI
- `google-generativeai>=0.3.0` - For Gemini integration

### 3. Configure SerpAPI Key

Add your SerpAPI key in the Settings → API Keys section:
- Service: `serp`
- Name: `SerpAPI Key`
- API Key: Your actual SerpAPI key

## 📱 Usage

### 1. Project Creation

When creating a new project, you'll see a new toggle:

```
[🔍 SerpAPI Research] [ON/OFF]
```

- **ON**: Will research topics before generating content
- **OFF**: Generate content directly without research

### 2. Content Generation Flow

#### With SerpAPI Enabled:
```
Project Creation → SerpAPI Research → Enhanced AI Generation → Blog Output
```

#### Without SerpAPI:
```
Project Creation → Direct AI Generation → Blog Output
```

### 3. Research Process

When SerpAPI is enabled, the system:

1. **Generates search queries** based on your project description
2. **Searches Google** using SerpAPI for relevant content
3. **Filters results** to remove social media, video platforms, etc.
4. **Extracts insights** and creates a research summary
5. **Enhances the AI prompt** with research findings
6. **Generates blogs** with current, well-researched content

## 🔍 API Endpoints

### Research Topic Endpoint

```http
POST /api/content-generation/research-topic
```

**Parameters:**
- `project_id`: Project UUID
- `topic`: Topic to research
- `api_key`: SerpAPI key
- `num_results`: Number of search results (default: 10)

**Response:**
```json
{
  "success": true,
  "project_id": "uuid",
  "topic": "artificial intelligence",
  "research_results": {
    "research_summary": "Research Summary for 'artificial intelligence':...",
    "external_links": [...],
    "key_insights": [...],
    "total_results": 15
  }
}
```

## 📊 Research Results

### Research Summary
A text summary of all found sources and their relevance to your topic.

### External Links
Up to 10 relevant external sources that can be referenced in your blog.

### Key Insights
Automatically extracted insights like:
- "Coverage of best practices related to the topic"
- "Comprehensive coverage from multiple sources"
- "Diverse perspectives from different websites"

## 🎯 How It Enhances Blog Generation

### Before (No SerpAPI):
```
AI Prompt: "Write a blog about digital marketing"
```

### After (With SerpAPI):
```
AI Prompt: "Write a blog about digital marketing

Research Insights:
Research Summary for 'digital marketing':
Found 12 relevant sources covering various aspects of digital marketing.

Key Sources:
1. Digital Marketing Trends 2024 (marketingtoday.com)
2. Complete Guide to Digital Marketing (digitalmarketinginstitute.com)
3. Best Practices for Digital Marketing (marketingprofs.com)

Research covers: marketingtoday.com, digitalmarketinginstitute.com, marketingprofs.com
Total relevant sources: 12

Key Insights:
• Coverage of best practices related to the topic
• Comprehensive coverage from multiple sources
• Diverse perspectives from different websites"
```

## 🧪 Testing

Run the test script to verify everything works:

```bash
python test_serpapi_integration.py
```

This will test:
1. The HTTP endpoint
2. The SerpAPI service directly
3. Error handling and response formats

## 🔒 Security & Rate Limits

### Rate Limiting
- 2-second delay between SerpAPI requests
- Maximum 5 search queries per research session
- Maximum 10 results per query

### Data Privacy
- Research results are stored in your project database
- No data is shared with third parties
- All requests use your own SerpAPI key

## 🚨 Troubleshooting

### Common Issues

1. **"No research results found"**
   - Check your SerpAPI key is valid
   - Verify the topic isn't too specific
   - Check SerpAPI service status

2. **"SerpAPI research failed"**
   - Verify API key permissions
   - Check network connectivity
   - Review SerpAPI usage limits

3. **"Project not found"**
   - Ensure project ID is valid UUID
   - Check database connection
   - Verify RLS policies

### Debug Mode

Enable detailed logging in the backend:

```python
# In backend/services/serp_api_service.py
logger.setLevel(logging.DEBUG)
```

## 📈 Performance

### Typical Research Times
- **Small topic** (1-2 queries): 5-10 seconds
- **Medium topic** (3-4 queries): 10-20 seconds
- **Large topic** (5 queries): 15-30 seconds

### Caching
- SerpAPI results are cached for 1 hour
- Research results are stored in project database
- Subsequent generations use cached research

## 🔮 Future Enhancements

Planned improvements:
- **AI-powered query generation** for better search terms
- **Content analysis** of research results
- **Automatic citation generation** for external sources
- **Research quality scoring** to improve results
- **Multi-language support** for international topics

## 📞 Support

If you encounter issues:

1. Check the logs in your backend console
2. Run the test script to isolate problems
3. Verify your SerpAPI key and permissions
4. Check the database migration was applied correctly

## 📚 Additional Resources

- [SerpAPI Documentation](https://serpapi.com/docs)
- [Google Search API Parameters](https://serpapi.com/docs/google-search-api)
- [Database Schema Updates](SUPABASE_SERPAPI_MIGRATION.sql)
- [Integration Test Script](test_serpapi_integration.py)

---

**Note**: This integration requires an active SerpAPI subscription. The free tier includes 100 searches per month.
